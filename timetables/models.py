from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import connection, models, transaction


class Timetable(models.Model):
    name = models.CharField(max_length=50)
    description = models.TextField(blank=True, default="")

    class Meta:
        ordering = ("name", "pk")
        verbose_name = "timetable"
        verbose_name_plural = "timetables"

    def __str__(self):
        return self.name


class StudentGroup(models.Model):
    name = models.CharField(max_length=50)
    size = models.PositiveIntegerField(validators=[MinValueValidator(1)])

    class Meta:
        ordering = ("name", "pk")
        verbose_name = "student group"
        verbose_name_plural = "student groups"

    def __str__(self):
        return self.name


class Subject(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, default="")

    class Meta:
        ordering = ("name", "pk")
        verbose_name = "subject"
        verbose_name_plural = "subjects"

    def __str__(self):
        return self.name


class Room(models.Model):
    name = models.CharField(max_length=50)
    capacity = models.PositiveIntegerField(validators=[MinValueValidator(1)])

    class Meta:
        ordering = ("name", "pk")
        verbose_name = "room"
        verbose_name_plural = "rooms"

    def __str__(self):
        return self.name


class Lesson(models.Model):
    class Weekday(models.TextChoices):
        MONDAY = "MON", "Monday"
        TUESDAY = "TUE", "Tuesday"
        WEDNESDAY = "WED", "Wednesday"
        THURSDAY = "THU", "Thursday"
        FRIDAY = "FRI", "Friday"
        SATURDAY = "SAT", "Saturday"
        SUNDAY = "SUN", "Sunday"

    timetable = models.ForeignKey(Timetable, on_delete=models.CASCADE, related_name="lessons")
    student_group = models.ForeignKey(StudentGroup, on_delete=models.PROTECT, related_name="lessons")
    subject = models.ForeignKey(Subject, on_delete=models.PROTECT, related_name="lessons")
    teacher = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="lessons")
    room = models.ForeignKey(Room, on_delete=models.PROTECT, related_name="lessons")
    weekday = models.CharField(max_length=3, choices=Weekday.choices)
    start_time = models.TimeField()
    end_time = models.TimeField()

    class Meta:
        ordering = ("weekday", "start_time", "pk")
        verbose_name = "lesson"
        verbose_name_plural = "lessons"

    def __str__(self):
        return f"{self.subject} — {self.get_weekday_display()} {self.start_time:%H:%M}–{self.end_time:%H:%M}"

    def clean(self):
        super().clean()
        errors = {}
        if self.teacher_id is not None:
            from .permissions import user_role
            if user_role(self.teacher) != 'TEACHER':
                errors['teacher'] = 'Teacher must have the TEACHER role.'
        if self.start_time is not None and self.end_time is not None:
            if self.end_time <= self.start_time:
                errors["end_time"] = "End time must be later than start time."
            elif self.weekday in self.Weekday.values:
                candidates = type(self).objects.filter(
                    weekday=self.weekday,
                    start_time__lt=self.end_time,
                    end_time__gt=self.start_time,
                )
                if self.pk is not None:
                    candidates = candidates.exclude(pk=self.pk)
                for field, label in (
                    ("room", "Room"),
                    ("teacher", "Teacher"),
                    ("student_group", "Student group"),
                ):
                    resource_id = getattr(self, f"{field}_id")
                    if resource_id is not None and candidates.filter(**{f"{field}_id": resource_id}).exists():
                        errors[field] = f"{label} is already booked for this time."
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        with transaction.atomic():
            lock_teacher_assignment(self.teacher_id)
            self.full_clean()
            return super().save(*args, **kwargs)


def lock_teacher_assignment(user_id):
    """Acquire SQLite's writer lock before checking role or lesson assignment."""
    if user_id is not None and connection.vendor == 'sqlite':
        from django.contrib.auth import get_user_model
        user_table = connection.ops.quote_name(get_user_model()._meta.db_table)
        with connection.cursor() as cursor:
            cursor.execute(f'UPDATE {user_table} SET last_login = last_login WHERE id = %s', [user_id])
