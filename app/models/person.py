from sqlalchemy import Column, Integer, String, Boolean, Date, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base


class Person(Base):
    __tablename__ = "tbl_j_person"
        
    person_id = Column("personID", Integer, primary_key=True, index=True)
    per_title = Column(String(50))
    per_first_name = Column("per_firstName", String(50), nullable=False)
    per_last_name = Column("per_lastName", String(50))
    per_gender = Column(String(6), nullable=False, default="male")
    per_date_of_birth = Column("per_dateOfBirth", Date)
    per_blood_group = Column("per_bloodGroup", String(50), default="unknown")
    per_nationality = Column(String(20), nullable=False, default="Bangladeshi")
    per_fathers_name = Column("per_fathersName", String(100))
    per_mothers_name = Column("per_mothersName", String(100))
    per_spouse_name = Column("per_spouseName", String(100))
    per_permanent_address = Column("per_permanentAddress", String(300))
    per_post_code = Column("per_postCode", String(50))
    per_telephone = Column(String(15))
    per_mobile = Column(String(15), nullable=False)
    per_email = Column(String(100))
    per_present_address = Column("per_presentAddress", String(300))
    per_marital_status = Column("per_maritalStatus", String(50), nullable=False, default="single")
    per_computer_literacy = Column("per_computerLiteracy", String(300))
    per_other_activities = Column("per_otherActivities", String(300))
    per_personal_statement = Column("per_personalStatment", Text)
    per_criminal_conviction = Column("per_criminalConviction", Boolean, nullable=False, default=False)
    per_conviction_details = Column("per_convictionDetails", Text)
    per_entry_date = Column("per_entryDate", Date, nullable=False, server_default=func.now())
    ex_per_ref = Column(String(2), nullable=False, default="s")
    ex_per_image = Column(Integer, default=0)

    # Relationship back to User    
    #user = relationship("User", back_populates="person")
    # --------------------
    # Python constants to mirror CHECK constraints
    # --------------------
    VALID_TITLES = ["Mr.", "Ms.", "Mrs.", "Dr.", "Prof.", "Engr.", "Adv."]
    VALID_GENDERS = ["male", "female"]
    VALID_BLOOD_GROUPS = ["O+", "A+", "B+", "AB+", "O-", "A-", "B-", "AB-", "unknown"]
    VALID_MARITAL_STATUSES = ["single", "married"]
    VALID_EX_PER_REF = ["e", "f", "s"]
