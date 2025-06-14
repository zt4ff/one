# EduHub MongoDB Project

## What the Project Is

EduHub is a sample educational platform backend built with MongoDB. It demonstrates how to model, seed, and query a learning management system (LMS) database, including students, instructors, courses, lessons, assignments, enrollments, and submissions. The project includes schema validation, realistic sample data.

---

## Prerequisites

- Python 3.8+
- [MongoDB Community Server](https://www.mongodb.com/try/download/community) (running locally on default port)
- All Python dependencies listed in `requirements.txt`

Install dependencies with:

```bash
pip install -r requirements.txt
```

---

## Running the Project

1. **Start MongoDB**  
   Make sure your MongoDB server is running locally.

2. **Seed the Database**  
   Run the notebook to create collections, apply schema validation, and seed sample data

---

## Collections and Schema Overview

### 1. `users`

- **Fields:** `userId` (string, unique), `email` (string, unique), `firstName`, `lastName`, `role` (`student` or `instructor`), `dateJoined` (date), `profile` (object: `bio`, `avatar`, `skills`), `isActive` (bool)
- **Indexes:** `email` (unique), `lastName` (for search)

### 2. `courses`

- **Fields:** `courseId` (string, unique), `title`, `description`, `instructorId` (ref: users), `category`, `level` (`beginner`, `intermediate`, `advanced`), `duration` (number), `price` (number), `tags` (array), `createdAt`, `updatedAt`, `isPublished` (bool), `rating` (number, 1-5)
- **Indexes:** `title` (text), `category`

### 3. `lessons`

- **Fields:** `lessonId` (string, unique), `courseId` (ref: courses), `title`, `content`, `order` (number), `resources` (array), `duration` (number), `createdAt`, `updatedAt`

### 4. `assignments`

- **Fields:** `assignmentId` (string, unique), `courseId` (ref: courses), `lessonId` (ref: lessons), `title`, `instructions`, `dueDate` (date), `maxScore` (number), `createdAt`, `updatedAt`
- **Indexes:** `dueDate`

### 5. `enrollments`

- **Fields:** `enrollmentId` (string, unique), `studentId` (ref: users), `courseId` (ref: courses), `enrollmentDate` (date), `progress` (0.0-1.0), `completed` (bool), `certificateIssued` (bool)
- **Indexes:** `studentId`, `courseId`

### 6. `submissions`

- **Fields:** `submissionId` (string, unique), `assignmentId` (ref: assignments), `studentId` (ref: users), `submissionDate` (date), `content`, `grade` (number), `feedback`, `gradedBy` (ref: users), `gradedAt` (date)

---

## Notes

- All collections use MongoDB schema validation (see `data/schema_validation.json`).
- Sample data is provided in `data/sample_data.json`.
- The project demonstrates best practices for indexing, aggregation, and schema design in MongoDB for an educational platform.

---
