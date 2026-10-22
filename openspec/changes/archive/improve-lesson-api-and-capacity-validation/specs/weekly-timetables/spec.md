# Spec Delta

## ADDED Requirements

### Requirement: Lesson room capacity
A lesson's student group size SHALL be less than or equal to its room capacity. The system SHALL preserve this invariant when lessons, student groups, or rooms are created or changed through the API, Django Admin, supported model writes, or direct SQLite writes.

#### Scenario: Create a lesson that fits
- **WHEN** a lesson is created with a student group whose size equals or is less than the room capacity
- **THEN** the lesson can be saved if its other fields are valid

#### Scenario: Reject an oversized group on a lesson
- **WHEN** a lesson is created or edited to pair a student group with a room whose capacity is smaller than the group's size
- **THEN** the write is rejected and no invalid lesson is stored

#### Scenario: Reject a group size increase
- **WHEN** an existing student group's size is increased beyond the capacity of any room used by one of its lessons
- **THEN** the update is rejected and the previous group size and lessons remain unchanged

#### Scenario: Reject a room capacity decrease
- **WHEN** an existing room's capacity is decreased below the size of any student group assigned to a lesson in that room
- **THEN** the update is rejected and the previous room capacity and lessons remain unchanged

#### Scenario: Reject a direct database write
- **WHEN** a direct SQLite insert or update of a lesson, or update of a student group or room, would break the capacity invariant
- **THEN** SQLite rejects the write without changing the stored valid values

### Requirement: Calendar ordering of lessons
Ordered lesson results SHALL use Monday, Tuesday, Wednesday, Thursday, Friday, Saturday, Sunday order, then ascending start time and lesson ID to break ties.

#### Scenario: Order lessons across weekdays
- **WHEN** lessons occur on Friday, Monday, and Wednesday
- **THEN** an ordered lesson result places Monday first, Wednesday second, and Friday third

#### Scenario: Order lessons within one weekday
- **WHEN** multiple lessons occur on the same weekday
- **THEN** they appear by start time, with ascending lesson ID for equal start times
