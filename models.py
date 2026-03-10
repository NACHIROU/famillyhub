import mongoengine as me
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date


class Family(me.Document):
    name = me.StringField(required=True, max_length=200)
    admin_id = me.ObjectIdField(required=True)
    created_at = me.DateTimeField(default=datetime.utcnow)


class User(UserMixin, me.Document):
    email = me.EmailField(required=True, unique=True, max_length=120)
    password_hash = me.StringField(required=True, max_length=256)
    name = me.StringField(required=True, max_length=100)
    phone = me.StringField(max_length=20)
    family_role = me.StringField(default='member', max_length=50)
    family_id = me.ObjectIdField()
    is_admin = me.BooleanField(default=False)
    created_at = me.DateTimeField(default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @staticmethod
    def get_by_email(email):
        return User.objects(email=email).first()

    @staticmethod
    def get_by_id(user_id):
        return User.objects(id=user_id).first()


class Meeting(me.Document):
    family_id = me.ObjectIdField(required=True)
    title = me.StringField(required=True, max_length=200)
    date_time = me.DateTimeField(required=True)
    location = me.StringField(max_length=200)
    agenda = me.StringField()
    themes_discussed = me.StringField()
    minutes = me.StringField()
    created_by = me.ObjectIdField(required=True)
    created_at = me.DateTimeField(default=datetime.utcnow)


class MeetingAttendance(me.Document):
    meeting_id = me.ObjectIdField(required=True)
    user_id = me.ObjectIdField(required=True)
    present = me.BooleanField(default=False)


class Decision(me.Document):
    family_id = me.ObjectIdField(required=True)
    meeting_id = me.ObjectIdField()
    title = me.StringField(required=True, max_length=200)
    description = me.StringField()
    status = me.StringField(default='pending', max_length=20)
    created_by = me.ObjectIdField(required=True)
    created_at = me.DateTimeField(default=datetime.utcnow)


class Vote(me.Document):
    family_id = me.ObjectIdField(required=True)
    decision_id = me.ObjectIdField()
    title = me.StringField(required=True, max_length=200)
    vote_type = me.StringField(required=True, max_length=20)
    options = me.StringField()
    deadline = me.DateTimeField()
    is_active = me.BooleanField(default=True)
    created_by = me.ObjectIdField(required=True)
    created_at = me.DateTimeField(default=datetime.utcnow)

    def get_options(self):
        import json
        if self.options:
            return json.loads(self.options)
        if self.vote_type == 'yes_no':
            return ['Yes', 'No']
        return []

    def get_results(self):
        responses = VoteResponse.objects(vote_id=self.id)
        results = {}
        for r in responses:
            results[r.response] = results.get(r.response, 0) + 1
        return results


class VoteResponse(me.Document):
    vote_id = me.ObjectIdField(required=True)
    user_id = me.ObjectIdField(required=True)
    response = me.StringField(required=True, max_length=100)
    created_at = me.DateTimeField(default=datetime.utcnow)


class Contribution(me.Document):
    family_id = me.ObjectIdField(required=True)
    title = me.StringField(required=True, max_length=200)
    amount = me.DecimalField(required=True, precision=2)
    frequency = me.StringField(default='one_time', max_length=20)
    due_date = me.DateField(required=True)
    created_by = me.ObjectIdField(required=True)
    created_at = me.DateTimeField(default=datetime.utcnow)


class Payment(me.Document):
    contribution_id = me.ObjectIdField(required=True)
    user_id = me.ObjectIdField(required=True)
    amount = me.DecimalField(required=True, precision=2)
    payment_date = me.DateField(required=True)
    status = me.StringField(default='paid', max_length=20)
    created_at = me.DateTimeField(default=datetime.utcnow)


class Document(me.Document):
    family_id = me.ObjectIdField(required=True)
    title = me.StringField(required=True, max_length=200)
    filename = me.StringField(required=True, max_length=300)
    file_path = me.StringField(required=True, max_length=500)
    file_type = me.StringField(max_length=50)
    uploaded_by = me.ObjectIdField(required=True)
    created_at = me.DateTimeField(default=datetime.utcnow)


class Notification(me.Document):
    user_id = me.ObjectIdField(required=True)
    title = me.StringField(required=True, max_length=200)
    message = me.StringField()
    type = me.StringField(max_length=50)
    is_read = me.BooleanField(default=False)
    created_at = me.DateTimeField(default=datetime.utcnow)
