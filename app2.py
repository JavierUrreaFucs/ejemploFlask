from flask import Flask, render_template, request, redirect, url_for, send_file, make_response
from flask_sqlalchemy import SQLAlchemy
import qrcode
from io import BytesIO

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://...'

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre1 = db.Column(db.String(80), nullable=False)
    nombre2 = db.Column(db.String(80), nullable=False)
    apellido1 = db.Column(db.String(80), nullable=False)
    apellido2 = db.Column(db.String(80), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    address = db.Column(db.String(200), nullable=True)
    org = db.Column(db.String(100), nullable=True)
    status = db.Column(db.String(20), nullable=False)

# Crear las tablas si no existen
with app.app_context():
    db.create_all()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate_qr/<int:contact_id>')
def generate_qr(contact_id):
    # Generar la URL que será codificada en el QR
    url_contacto = url_for('view_contact', contact_id=contact_id, _external=True)

    # Generar el código QR con la URL
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(url_contacto)
    qr.make(fit=True)

    qr_img = qr.make_image(fill='black', back_color='white')

    # Guardar el QR en un buffer
    buffer = BytesIO()
    qr_img.save(buffer, 'PNG')
    buffer.seek(0)

    # Enviar el código QR como respuesta
    return send_file(buffer, mimetype='image/png')

@app.route('/contact_info/<int:contact_id>')
def view_contact(contact_id):
    contact = User.query.get(contact_id)

    # Verificar si el contacto existe y está activo
    if contact is None or contact.status != 'active':
        return "El contacto no está disponible.", 403

    # Generar vCard
    vcard = f"""BEGIN:VCARD
VERSION:3.0
N:{contact.apellido2};{contact.nombre2};{contact.apellido1};{contact.nombre1}
FN:{contact.nombre1} {contact.nombre2} {contact.apellido1} {contact.apellido2}
TEL;TYPE=WORK,VOICE:{contact.phone}
EMAIL:{contact.email}
ORG:{contact.org}
ADR;TYPE=work:;;{contact.address};;;;
END:VCARD"""

    # Crear la respuesta para el archivo vCard
    response = make_response(vcard)
    response.headers["Content-Disposition"] = f"attachment; filename={contact.nombre1}_{contact.apellido1}.vcf"
    response.headers["Content-Type"] = "text/vcard"

    return response

if __name__ == '__main__':
    app.run(debug=True)
