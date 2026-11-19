from .user import User
from .person import Person
from .result_final_exam import ResultFinalExam
from .student_record import StudentRecord
from app.models.registration_application import RegistrationApplication
from app.models.registration_application_detail import RegistrationApplicationDetail
from app.models.registration_application_history import RegistrationApplicationHistory
__all__ = [
    "RegistrationApplication",
    "RegistrationApplicationDetail",
    "RegistrationApplicationHistory",
]