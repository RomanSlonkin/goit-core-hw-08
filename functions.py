from collections import UserDict
from datetime import datetime, timedelta
import pickle

class Field:
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)

class Name(Field):
    def __init__(self, value):
        if not value:
            raise ValueError("Name could not be empty.")
        super().__init__(value)

class Phone(Field):
    def __init__(self, value):
        if not(value.isdigit() and len(value) == 10):
            raise ValueError("Phone number must be 10 numbers")
        super().__init__(value)

class Birthday(Field):
    def __init__(self, value):
        if not datetime.strptime(value, '%d-%m-%Y').date():
            raise ValueError("Birthday must be in the format 'DD-MM-YYYY'")
        super().__init__(value)

class Record:
    def __init__(self, name):
        self.name = Name(name)
        self.phones = []
        self.birthday = None
    
    def add_phone(self, phone):
        phone = Phone(phone)
        self.phones.append(phone)

    def remove_phone(self, phone):
        for p in self.phones:
            if p.value == phone:
                return self.phones.remove(p)
        return("There is no such phone in the contact list.")

    def edit_phone(self, old_phone, new_phone):
        old_phone = Phone(old_phone)
        new_phone = Phone(new_phone)
        for idx, phone in enumerate(self.phones):
            if phone.value == old_phone.value:
                self.phones[idx] = new_phone
                return
        raise ValueError("There is no such phone in the contact list.")     

    def find_phone(self, phone):
        phone = Phone(phone)
        for p in self.phones:
            if p.value == phone.value:
                return p
        return None

    def __str__(self):
        birthday_str = self.birthday.value if self.birthday else 'No information'
        return f"Contact name: {self.name.value}, phones: {'; '.join(p.value for p in self.phones)}, birthday: {birthday_str}"
    
    def add_birthday(self, date):
        self.birthday = Birthday(date)


class AddressBook(UserDict):
    def add_record(self, record):
        self.data[record.name.value] = record

    def delete(self, name):
        if name in self.data:
            del self.data[name]
        else:
             return "There is no contact with this name."

    def find(self, name):
        return self.data.get(name, None)
    
    def get_upcoming_birthdays(self):
        def find_next_weekday(start_date, weekday):
            days_ahead = weekday - start_date.weekday()
            if days_ahead <= 0:
                days_ahead += 7
            return start_date + timedelta(days=days_ahead)
        
        def adjust_for_weekend(birthday):
            if birthday.weekday() >= 5:
                return find_next_weekday(birthday, 0)
            return birthday
        
        today = datetime.now().date()
        upcoming_birthdays = []
        for record in self.data.values():
            if record.birthday is not None:
                birthday = datetime.strptime(record.birthday.value, '%d-%m-%Y').date()
                birth_this_year = birthday.replace(year=today.year)
                if 0 <= (birth_this_year - today).days <= 7:
                    if birth_this_year.weekday() in (5, 6):
                        cong_date = adjust_for_weekend(birth_this_year)
                    else:
                        cong_date = birth_this_year
                    upcoming_birthdays.append({'Name': record.name.value, 'Birthday': cong_date.strftime('%d-%m-%Y')})
        return upcoming_birthdays
    
    def __str__(self):
        contacts = [str(record) for record in self.data.values()]
        return "\n".join(contacts)
    
    def __getstate__(self):
        state = self.__dict__.copy()
        state['data'] = {k: pickle.dumps(v) for k, v in state['data'].items()}
        return state  
    
    def __setstate__(self, state):
        state['data'] = {k: pickle.loads(v) for k, v in state['data'].items()}
        self.__dict__.update(state)


def input_error(func):
    def handler(*args):
        try:
            return func(*args)
        except (ValueError):
            return'Please give me: name phone_number'
        except KeyError:
            return 'There is no such contact in database!'
        except IndexError:
            return 'Please give me name!'
    return handler

@input_error
def parse_input(user_input):
    cmd, *args = user_input.split()
    cmd = cmd.strip().lower()
    return cmd, *args

@input_error
def add_contact(args, book: AddressBook):
    name, phone, *_ = args
    record = book.find(name)
    message = "Contact updated."
    if record is None:
        record = Record(name)
        book.add_record(record)
        message = "Contact added."
    if phone:
        record.add_phone(phone)
    return message

@input_error
def change_contact(args, book: AddressBook):
    name, old_phone, new_phone = args
    record = book.find(name)
    if record is None:
        return 'There is no such contact, try command: add'
    else:
        record.edit_phone(old_phone, new_phone)        
        return f'Old contact: {name} {old_phone}. Updated to: {new_phone}'

@input_error
def phone_number(args, book: AddressBook):
    name = args[0]
    record = book.find(name)
    if record:
        return f"{record.name.value}: {'; '.join(p.value for p in record.phones)} "
    else:
        raise KeyError
    
    
def all_numbers(book: AddressBook):
    return book.__str__()


@input_error
def add_birthday(args, book: AddressBook):
    name, date = args
    record = book.find(name)
    if record:
        record.add_birthday(date)
        return f'Birthday for {name} set to {date}.'
    else:
        return 'There is no such contact, try command: add'

@input_error
def show_birthday(args, book: AddressBook):
    name = args[0]
    record = book.find(name)
    if record:
        if record.birthday is not None:
            return f'Birthday for {name}: {record.birthday.value}'
        else:
            return 'No birthday set for this contact.'
    else:
        return 'There is no such contact'

@input_error
def birthdays(book: AddressBook):
    upcoming_birthdays = book.get_upcoming_birthdays()
    if upcoming_birthdays:
        return 'Upcoming birthdays:\n' + '\n'.join(
            f"{item['Name']}: {item['Birthday']}" for item in upcoming_birthdays
        )
    else:
        return 'No upcoming birthdays.'
    
def save_data(book: AddressBook, filename='addressbook.pkl'):
    with open(filename, 'wb') as f:
        pickle.dump(book, f)

def load_data(filename='addressbook.pkl'):
    try:
        with open(filename, 'rb') as f:
            return pickle.load(f)
    except FileNotFoundError:
        return AddressBook()
