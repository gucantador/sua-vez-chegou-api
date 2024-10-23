from . import db


# Modelo Costumer
class Costumer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    phone = db.Column(db.String(15), nullable=False)
    position_in_line = db.Column(db.Integer, nullable=False)
    is_turn = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f'<Costumer {self.id}>'

    def to_dict(self):
        return {
            'id': str(self.id),
            'phone': self.phone,
            'position_in_line': self.position_in_line,
            'is_turn': self.is_turn
        }


# Modelo User
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'adm', 'operator'

    company = db.relationship("Company", backref="users")

    def __repr__(self):
        return f'<User {self.username}>'

    def to_dict(self):
        return {
            'id': str(self.id),
            'username': self.username,
            'email': self.email,
            'company': self.company_id,
            'role': self.role
        }


# Modelo Company
class Company(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)
    cnpj = db.Column(db.String(18), unique=True, nullable=False)

    def __repr__(self):
        return f'<Company {self.name}>'

    def to_dict(self):
        return {
            'id': str(self.id),
            'name': self.name,
            'cnpj': self.cnpj
        }


# Modelo Line
class Line(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, nullable=False)
    currentCode = db.Column(db.Integer, nullable=False)
    lastCode = db.Column(db.Integer, nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)

    company = db.relationship("Company", backref="lines")

    def __repr__(self):
        return f'<Line {self.id}>'

    def to_dict(self):
        return {
            'id': str(self.id),
            'date': self.date.isoformat(),
            'currentCode': self.currentCode,
            'lastCode': self.lastCode,
            'company_id': self.company_id
        }


