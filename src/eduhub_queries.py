from pymongo import MongoClient
import json
from helper import Helper
from pymongo.errors import DuplicateKeyError, WriteError


class EdHubDB:
    def __init__(self):
        # Initialize helperclass
        self.helper = Helper()

        # File paths
        self.schemas_path = "../data/schema_validation.json"
        self.sample_data_path = "../data/sample_data.json"

        self.connection_url = "mongodb://localhost:27017/"
        self.database_name = "eduhub_db"
        self.client = MongoClient(self.connection_url)
        self.db = self.client[self.database_name]

        # drop existing collections to start afresh
        for collection in self.db.list_collection_names():
            self.db[collection].drop()

        # collections
        self.users_col = self.db["users"]
        self.courses_col = self.db["courses"]
        self.enrollments_col = self.db["enrollments"]
        self.lessons_col = self.db["lessons"]
        self.assignments_col = self.db["assignments"]
        self.submissions_col = self.db["submissions"]

    # Part 1
    def load_schemas(self):
        """Load validation schemas from JSON file"""
        try:
            with open(self.schemas_path, "r") as f:
                schemas = json.load(f)
            return schemas
        except FileNotFoundError:
            raise FileNotFoundError(f"Schema file not found: {self.schemas_path}")
        except json.JSONDecodeError:
            raise ValueError(f"Invalid JSON in schema file: {self.schemas_path}")

    def build_collection(self):
        """Setup collections and validations from JSON files"""

        schemas = self.load_schemas()

        try:
            for collection_name, validator in schemas.items():
                self.db.create_collection(collection_name, validator=validator)
                print(f"Created collection: {collection_name}")
        except Exception as e:
            print(f"Error initializing database: {e}")
            raise

    # Part 2
    def seed_database(self):
        """Seed all collections with sample data, converting date fields using schema."""
        try:
            with open(self.sample_data_path, "r") as f:
                data = json.load(f)
            with open(self.schemas_path, "r") as f:
                schemas = json.load(f)
        except FileNotFoundError as e:
            raise FileNotFoundError(str(e))
        except json.JSONDecodeError as e:
            raise ValueError(str(e))

        for collection_name, documents in data.items():
            if isinstance(documents, list) and collection_name in schemas:
                date_fields = self.helper.get_date_fields(
                    schemas[collection_name]["$jsonSchema"]
                )
                documents = [
                    self.helper.convert_dates_by_schema(doc, date_fields)
                    for doc in documents
                ]
                if documents:
                    self.db[collection_name].insert_many(documents)
                    print(
                        f"Seeded {len(documents)} documents into '{collection_name}' collection."
                    )
            else:
                print(
                    f"Warning: Data for '{collection_name}' is not a list or schema missing, skipping."
                )

    ## Part 3 Basic CRUD operations
    def insert_student(self, data):
        """Insert a new student document into the users collection."""
        try:
            # Ensure role is a student
            data["role"] = "student"
            result = self.users_col.insert_one(data)
            return result
        except Exception as e:
            print(f"Unexpected error inserting student: {e}")
        return None

    def insert_course(self, data):
        """Insert a new course document into the courses collection."""
        try:
            result = self.courses_col.insert_one(data)
            return result.inserted_id
        except Exception as e:
            print(f"Unexpected error inserting course: {e}")
        return None

    def register_student(self, student_id, course_id):
        """Register a student to a course (create an enrollment)."""
        enrollment = {
            "enrollmentId": f"e{self.enrollments_col.count_documents({}) + 1}",
            "studentId": student_id,
            "courseId": course_id,
            "enrollmentDate": self.helper.faker.date_time(),
            "progress": 0.0,
            "completed": False,
            "certificateIssued": False,
        }
        try:
            result = self.enrollments_col.insert_one(enrollment)
            return result.inserted_id
        except Exception as e:
            print(f"Unexpected error registering student: {e}")
        return None

    def insert_lesson(self, data):
        """Add a lesson to a course (insert into lessons collection)."""
        try:
            result = self.lessons_col.insert_one(data)
            return result
        except Exception as e:
            print(f"Unexpected error adding lesson: {e}")
        return None

    def get_active_students(self):
        """Find all active students"""
        try:
            students = list(self.users_col.find({"role": "student", "isActive": True}))
            return students
        except Exception as e:
            print(f"Error fetching active students: {e}")
            return []

    def get_course_details(self):
        """Retrieve course details with instructor information"""
        try:
            pipeline = [
                {
                    "$lookup": {
                        "from": "users",
                        "localField": "instructorId",
                        "foreignField": "userId",
                        "as": "instructor",
                    }
                },
                {"$unwind": "$instructor"},
            ]
            courses = list(self.courses_col.aggregate(pipeline))
            return courses
        except Exception as e:
            print(f"Error fetching course details: {e}")
            return []

    def get_courses_by_category(self, category):
        """Get all courses in a specific category"""
        try:
            courses = list(self.courses_col.find({"category": category}))
            return courses
        except Exception as e:
            print(f"Error fetching courses by category: {e}")
            return []

    def get_student_enrolled_to_course(self, course_id):
        """Find students enrolled in a particular course"""
        try:
            enrollments = self.enrollments_col.find({"courseId": course_id})
            student_ids = [enr["studentId"] for enr in enrollments]
            students = list(self.users_col.find({"userId": {"$in": student_ids}}))
            return students
        except Exception as e:
            print(f"Error fetching students enrolled to course: {e}")
            return []

    def search_courses_by_title(self, title):
        """Search courses by title (case-insensitive, partial match)"""
        try:
            courses = list(
                self.courses_col.find({"title": {"$regex": title, "$options": "i"}})
            )
            return courses
        except Exception as e:
            print(f"Error searching courses by title: {e}")
            return []

    def modify_profile(self, user_id, updates):
        """Update a user’s profile information"""
        try:
            result = self.users_col.update_one(
                {"userId": user_id}, {"$set": {"profile": updates}}
            )
            if result.matched_count == 0:
                print(f"No user found with userId: {user_id}")
                return False
            return True
        except Exception as e:
            print(f"Error updating profile: {e}")
            return False

    def publish_course(self, course_id):
        """Mark a course as published"""
        try:
            result = self.courses_col.update_one(
                {"courseId": course_id}, {"$set": {"isPublished": True}}
            )
            if result.matched_count == 0:
                print(f"No course found with courseId: {course_id}")
                return False
            return True
        except Exception as e:
            print(f"Error publishing course: {e}")
            return False

    def update_assignment_grade(self, submission_id, grade, feedback=None):
        """Update assignment grades"""
        try:
            update_fields = {"grade": grade}
            if feedback is not None:
                update_fields["feedback"] = feedback
            result = self.submissions_col.update_one(
                {"submissionId": submission_id}, {"$set": update_fields}
            )
            if result.matched_count == 0:
                print(f"No submission found with submissionId: {submission_id}")
                return False
            return True
        except Exception as e:
            print(f"Error updating assignment grade: {e}")
            return False

    def add_tags_to_course(self, course_id, tags):
        """Add tags to an existing course"""
        try:
            result = self.courses_col.update_one(
                {"courseId": course_id}, {"$addToSet": {"tags": {"$each": tags}}}
            )
            if result.matched_count == 0:
                print(f"No course found with courseId: {course_id}")
                return False
            return True
        except Exception as e:
            print(f"Error adding tags to course: {e}")
            return False

    def deactivate_user(self, user_id):
        """Remove a user (soft delete by setting isActive to false)"""
        try:
            result = self.users_col.update_one(
                {"userId": user_id}, {"$set": {"isActive": False}}
            )
            if result.matched_count == 0:
                print(f"No user found with userId: {user_id}")
                return False
            return True
        except Exception as e:
            print(f"Error deactivating user: {e}")
            return False

    def delete_enrollment(self, enrollment_id):
        """Delete an enrollment"""
        try:
            result = self.enrollments_col.delete_one({"enrollmentId": enrollment_id})
            if result.deleted_count == 0:
                print(f"No enrollment found with enrollmentId: {enrollment_id}")
                return False
            return True
        except Exception as e:
            print(f"Error deleting enrollment: {e}")
            return False

    def remove_lesson_from_course(self, lesson_id, course_id):
        """Remove a lesson from a course"""
        try:
            result = self.lessons_col.delete_one(
                {"lessonId": lesson_id, "courseId": course_id}
            )
            if result.deleted_count == 0:
                print(
                    f"No lesson found with lessonId: {lesson_id} in courseId: {course_id}"
                )
                return False
            return True
        except Exception as e:
            print(f"Error removing lesson from course: {e}")
            return False

    # Part 4: Advanced Queries and Aggregation
