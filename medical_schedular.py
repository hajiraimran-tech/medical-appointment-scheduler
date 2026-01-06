# MEDICAL APPOINTMENT SCHEDULER
# A comprehensive system for managing patient-doctor appointments with conflict resolution and JSON persistence.

import json
from datetime import datetime, timedelta
import os

class Person:
    def __init__(self, name, contact, person_type="patient"):
        self.name = name
        self.contact = contact
        self.person_type = person_type  
        self.id = None
    
    def display_info(self):
        return f"Name: {self.name}, Contact: {self.contact}, ID: {self.id}"
    
    def to_dict(self):
        return {
            'name': self.name,
            'contact': self.contact,
            'id': self.id
        }
    
    @classmethod
    def from_dict(cls, data):
        person = cls(data['name'], data['contact'])
        person.id = data['id'] 
        return person

class Patient(Person):
    def __init__(self, name, contact, age=None):
        super().__init__(name, contact, person_type="patient")
        self.age = age
        self.medical_history = []
        self.is_active = True
    
    def display_info(self):
        base_info = super().display_info()
        age_info = f", Age: {self.age}" if self.age else ""
        return f"PATIENT - {base_info}{age_info}"
    
    def add_to_history(self, appointment):
        self.medical_history.append(appointment)
    
    def to_dict(self):
        data = super().to_dict()
        data.update({
            'age': self.age,
            'is_active': self.is_active,
            'medical_history': [app.id for app in self.medical_history] if self.medical_history else []
        })
        return data

class Doctor(Person):
    def __init__(self, name, contact, specialization):
        super().__init__(name, contact, person_type="doctor")
        self.specialization = specialization
        self.appointments = []
        self.working_hours = {
            'start': '09:00',
            'end': '17:00',
            'days': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
        }
    
    def display_info(self):
        base_info = super().display_info()
        return f"DOCTOR - {base_info}, Specialization: {self.specialization}"
    
    def is_available(self, appointment_datetime):
        for existing_appointment in self.appointments:
            if existing_appointment.datetime == appointment_datetime:
                return False  
        return True
    
    def to_dict(self):
        data = super().to_dict()
        data.update({
            'specialization': self.specialization,
            'working_hours': self.working_hours,
            'appointments': [app.id for app in self.appointments] if self.appointments else []
        })
        return data

class Appointment:
    def __init__(self, patient, doctor, appointment_datetime, duration_minutes=30):
        self.patient = patient
        self.doctor = doctor
        self.datetime = appointment_datetime
        self.duration = duration_minutes
        self.status = "Scheduled"
        self.notes = ""
        self.id = None
        
        patient.add_to_history(self)
        doctor.appointments.append(self)
    
    def reschedule(self, new_datetime):
        if self.doctor.is_available(new_datetime):
            old_time = self.datetime
            self.datetime = new_datetime
            self.status = "Rescheduled"
            return f"Appointment rescheduled from {old_time} to {new_datetime}"
        else:
            return f"Doctor NOT available at {new_datetime}"
    
    def complete(self, notes=""):
        self.status = "Completed"
        self.notes = notes
        return f"Appointment marked as completed"
    
    def cancel(self):
        self.status = "Cancelled"
        if self in self.doctor.appointments:
            self.doctor.appointments.remove(self)
        return f"Appointment cancelled!"
    
    def display_info(self):
        return f"""
        APPOINTMENT {self.id}
        Patient: {self.patient.name}
        Doctor: {self.doctor.name} ({self.doctor.specialization})
        Time: {self.datetime.strftime('%Y-%m-%d %I:%M %p')}
        Duration: {self.duration} minutes
        Status: {self.status}
        """
    
    def to_dict(self):
        return {
            'id': self.id,
            'patient_id': self.patient.id,
            'doctor_id': self.doctor.id,
            'datetime': self.datetime.strftime('%Y-%m-%d %H:%M:%S'),
            'duration': self.duration,
            'status': self.status,
            'notes': self.notes
        }

class HospitalSystem:
    def __init__(self):
        self._patients = []     
        self._doctors = []      
        self._appointments = []  
        self.data_file = "hospital_data.json"
        self._load_data()  
    
    def add_patient(self, name, contact, age=None):
        max_id = 0
        for patient in self._patients:
            if patient.id and patient.id.startswith('P'):
                try:
                    num = int(patient.id[1:])
                    if num > max_id:
                        max_id = num
                except:
                    pass
        
        patient = Patient(name, contact, age)
        patient.id = f"P{max_id + 1}"
        self._patients.append(patient)
        self._save_data()
        print(f"Patient added: {patient.display_info()}")
        return patient
    
    def find_patient_by_id(self, patient_id):
        for patient in self._patients:
            if patient.id == patient_id:
                return patient
        return None
    
    def add_doctor(self, name, contact, specialization):
        max_id = 0
        for doctor in self._doctors:
            if doctor.id and doctor.id.startswith('D'):
                try:
                    num = int(doctor.id[1:])
                    if num > max_id:
                        max_id = num
                except:
                    pass
        
        doctor = Doctor(name, contact, specialization)
        doctor.id = f"D{max_id + 1}"
        self._doctors.append(doctor)
        self._save_data()
        print(f"Doctor added: {doctor.display_info()}")
        return doctor
    
    def find_doctor_by_id(self, doctor_id):
        for doctor in self._doctors:
            if doctor.id == doctor_id:
                return doctor
        return None
    
    def schedule_appointment(self, patient_id, doctor_id, appointment_datetime):
        patient = self.find_patient_by_id(patient_id)
        doctor = self.find_doctor_by_id(doctor_id)
        
        if not patient:
            return f"Patient with ID {patient_id} not found"
        if not doctor:
            return f"Doctor with ID {doctor_id} not found"
        
        if not doctor.is_available(appointment_datetime):
            return f"Doctor {doctor.name} is not available at {appointment_datetime}"
        
        appointment_time = appointment_datetime.time()
        working_start = datetime.strptime(doctor.working_hours['start'], '%H:%M').time()
        working_end = datetime.strptime(doctor.working_hours['end'], '%H:%M').time()
        
        if not (working_start <= appointment_time <= working_end):
            return f"Appointment time is outside doctor's working hours ({doctor.working_hours['start']} to {doctor.working_hours['end']})"
        
        day_name = appointment_datetime.strftime('%A')
        if day_name not in doctor.working_hours['days']:
            return f"{day_name} is not a working day for this doctor"
        
        appointment = Appointment(patient, doctor, appointment_datetime)
        
        max_id = 0
        for app in self._appointments:
            if app.id and app.id.startswith('A'):
                try:
                    num = int(app.id[1:])
                    if num > max_id:
                        max_id = num
                except:
                    pass
        
        appointment.id = f"A{max_id + 1}"
        self._appointments.append(appointment)
        self._save_data()
        
        return f"Appointment scheduled successfully!\n{appointment.display_info()}"
    
    def view_appointments(self, filter_type="all", id=None):
        filtered_appointments = []
        
        if filter_type == "all":
            filtered_appointments = self._appointments
        elif filter_type == "patient" and id:
            patient = self.find_patient_by_id(id)
            if patient:
                filtered_appointments = patient.medical_history
        elif filter_type == "doctor" and id:
            doctor = self.find_doctor_by_id(id)
            if doctor:
                filtered_appointments = doctor.appointments
        elif filter_type == "today":
            today = datetime.now().date()
            filtered_appointments = [app for app in self._appointments 
                                   if app.datetime.date() == today]
        
        if not filtered_appointments:
            return "No appointments found."
        
        result = f"\nAPPOINTMENTS ({len(filtered_appointments)} found):\n"
        for i, app in enumerate(filtered_appointments, 1):
            result += f"\n{i}. {app.display_info()}"
        
        return result
    
    def _save_data(self):
        data = {
            'patients': [p.to_dict() for p in self._patients],
            'doctors': [d.to_dict() for d in self._doctors],
            'appointments': [a.to_dict() for a in self._appointments]
        }
        
        try:
            with open(self.data_file, 'w') as f:
                json.dump(data, f, indent=4)
            print(f"Data saved to {self.data_file}")
        except Exception as e:
            print(f"Error saving data: {e}")
    
    def _load_data(self):
        if not os.path.exists(self.data_file):
            print("No existing data found. Starting fresh.")
            return
        
        try:
            with open(self.data_file, 'r') as f:
                data = json.load(f)
            
            self._patients = []
            self._doctors = []
            self._appointments = []

            for patient_data in data.get('patients', []):
                patient = Patient.from_dict(patient_data)
                patient.age = patient_data.get('age')
                patient.is_active = patient_data.get('is_active', True)
                self._patients.append(patient)
            
            for doctor_data in data.get('doctors', []):
                doctor = Doctor.from_dict(doctor_data)
                doctor.specialization = doctor_data.get('specialization')
                doctor.working_hours = doctor_data.get('working_hours', 
                    {'start': '09:00', 'end': '17:00', 'days': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']})
                self._doctors.append(doctor)
            
            for app_data in data.get('appointments', []):
                patient = self.find_patient_by_id(app_data['patient_id'])
                doctor = self.find_doctor_by_id(app_data['doctor_id'])
                
                if patient and doctor:
                    app_datetime = datetime.strptime(app_data['datetime'], '%Y-%m-%d %H:%M:%S')
                    
                    appointment = Appointment(patient, doctor, app_datetime, 
                                            app_data.get('duration', 30))
                    
                    appointment.id = app_data['id']
                    appointment.status = app_data['status']
                    appointment.notes = app_data.get('notes', '')
                    
                    self._appointments.append(appointment)
            
            print(f"Loaded {len(self._patients)} patients, {len(self._doctors)} doctors, {len(self._appointments)} appointments")
            
        except Exception as e:
            print(f"Error loading data: {e}")
    
    def get_statistics(self):
        total_patients = len(self._patients)
        total_doctors = len(self._doctors)
        total_appointments = len(self._appointments)
        
        status_count = {}
        for app in self._appointments:
            status_count[app.status] = status_count.get(app.status, 0) + 1
        
        stats = f"""
        HOSPITAL SYSTEM STATISTICS
        Patients: {total_patients}
        Doctors: {total_doctors}
        Appointments: {total_appointments}
        
        Appointment Status:
        """
        for status, count in status_count.items():
            stats += f"  {status}: {count}\n"
        
        return stats
    
    def display_all_people(self):
        result = "\nALL PEOPLE IN SYSTEM:\n"
        result += "\nPATIENTS:\n" + "="*30
        for patient in self._patients:
            result += f"\n{patient.display_info()}"
        
        result += "\n\nDOCTORS:\n" + "="*30
        for doctor in self._doctors:
            result += f"\n{doctor.display_info()}"
        
        return result

def display_menu():
    print("\nMEDICAL APPOINTMENT SCHEDULER\n")
    print("1. Add Patient")
    print("2. Add Doctor")
    print("3. Schedule Appointment")
    print("4. View Appointments")
    print("5. View All People")
    print("6. System Statistics")
    print("7. Test Conflict Detection")
    print("8. Exit")

def get_datetime_input(prompt):
    while True:
        try:
            date_str = input(f"{prompt} (YYYY-MM-DD HH:MM): ")
            return datetime.strptime(date_str, '%Y-%m-d %H:%M')
        except ValueError:
            print("Invalid format. Please use YYYY-MM-DD HH:MM (e.g., 2024-02-20 14:30)")

def main():
    system = HospitalSystem()
    
    while True:
        display_menu()
        choice = input("\nEnter your choice (1-8): ").strip()
        
        if choice == "1":
            print("\nADD NEW PATIENT")
            name = input("Patient Name: ").strip()
            contact = input("Contact Info: ").strip()
            age = input("Age (optional, press Enter to skip): ").strip()
            age = int(age) if age.isdigit() else None
            system.add_patient(name, contact, age)
        
        elif choice == "2":
            print("\nADD NEW DOCTOR")
            name = input("Doctor Name: ").strip()
            contact = input("Contact Info: ").strip()
            specialization = input("Specialization: ").strip()
            system.add_doctor(name, contact, specialization)
        
        elif choice == "3":
            print("\nSCHEDULE APPOINTMENT")
            
            if system._patients:
                print("\nAvailable Patients:")
                for patient in system._patients:
                    print(f"  ID: {patient.id}, Name: {patient.name}")
            else:
                print("No patients available. Please add a patient first.")
                continue
            
            if system._doctors:
                print("\nAvailable Doctors:")
                for doctor in system._doctors:
                    print(f"  ID: {doctor.id}, Name: {doctor.name}, Specialization: {doctor.specialization}")
            else:
                print("No doctors available. Please add a doctor first.")
                continue
            
            patient_id = input("\nEnter Patient ID: ").strip()
            doctor_id = input("Enter Doctor ID: ").strip()
            appointment_time = get_datetime_input("Enter Appointment Date/Time")
            
            result = system.schedule_appointment(patient_id, doctor_id, appointment_time)
            print(f"\n{result}")
        
        elif choice == "4":
            print("\nVIEW APPOINTMENTS")
            print("1. View All Appointments")
            print("2. View by Patient")
            print("3. View by Doctor")
            print("4. View Today's Appointments")
            
            view_choice = input("\nChoose view option (1-4): ").strip()
            
            if view_choice == "1":
                print(system.view_appointments("all"))
            elif view_choice == "2":
                patient_id = input("Enter Patient ID: ").strip()
                print(system.view_appointments("patient", patient_id))
            elif view_choice == "3":
                doctor_id = input("Enter Doctor ID: ").strip()
                print(system.view_appointments("doctor", doctor_id))
            elif view_choice == "4":
                print(system.view_appointments("today"))
            else:
                print("Invalid choice")
        
        elif choice == "5":
            print(system.display_all_people())
        
        elif choice == "6":
            print(system.get_statistics())
        
        elif choice == "7":
            print("\nTEST CONFLICT DETECTION")
            if len(system._doctors) >= 1 and len(system._patients) >= 1:
                doctor = system._doctors[0]
                patient = system._patients[0]
                
                test_time = datetime.now().replace(hour=10, minute=0, second=0, microsecond=0)
                result1 = system.schedule_appointment(patient.id, doctor.id, test_time)
                print(f"First appointment: {result1}")
                
                result2 = system.schedule_appointment(patient.id, doctor.id, test_time)
                print(f"Conflicting appointment attempt: {result2}")
                
                non_conflict_time = test_time + timedelta(hours=1)
                result3 = system.schedule_appointment(patient.id, doctor.id, non_conflict_time)
                print(f"Non-conflicting appointment: {result3}")
            else:
                print("Need at least 1 doctor and 1 patient to test")
        
        elif choice == "8":
            print("\nSaving data...")
            system._save_data()
            print("Thank you for using Medical Appointment Scheduler!")
            break
        
        else:
            print("Invalid choice. Please enter 1-8.")
        
        input("\nPress Enter to continue...")

if __name__ == "__main__":
    main()