from flask import Flask, render_template, request, redirect, url_for, send_file, make_response
from flask_sqlalchemy import SQLAlchemy
import qrcode
from io import BytesIO
#from flask_mysqldb import MySQL

app = Flask(__name__)

# Configuración de la base de datos MySQL
#app.config['MYSQL_HOST'] = 'localhost'
#app.config['MYSQL_USER'] = 'root'
#app.config['MYSQL_PASSWORD'] = ''
#app.config['MYSQL_DB'] = 'contact_db'
#
#mysql = MySQL(app)

# Obtén la URL de la base de datos desde la variable de entorno
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://contact_db_uicb_user:6Nf9WYZDrfH6ot5014l9e3CRu8YCf6ZO@dpg-cs8i9idsvqrc73bs3s1g-a.oregon-postgres.render.com/contact_db_uicb'

# Inicializa la base de datos
db = SQLAlchemy(app)

# Define tus modelos aquí
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

    def __repr__(self):
        return f'<User {self.nombre1} {self.apellido1}>'

# Crear las tablas en la base de datos
with app.app_context():
    db.create_all()


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/add_contact', methods=['POST'])
def add_contact():
    if request.method == 'POST':
        nombre1 = request.form['nombre1']
        nombre2 = request.form['nombre2']
        apellido1 = request.form['apellido1']
        apellido2 = request.form['apellido2']
        phone = request.form['phone']
        email = request.form['email']
        address = request.form['address']
        org = request.form['org']

        # Insertar los datos en la base de datos con el status 'active'
        #cursor = mysql.connection.cursor()
        #cursor.execute("""
        #    INSERT INTO contacts (nombre1, nombre2, apellido1, apellido2, phone, email, address, org, status)
        #    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'active')
        #""", (nombre1, nombre2, apellido1, apellido2, phone, email, address, org))
        #mysql.connection.commit()
        #contact_id = cursor.lastrowid
        #cursor.close()
        #return redirect(url_for('generate_qr', contact_id=contact_id))

        # Crear un nuevo usuario usando el modelo
        new_contact = User(
            nombre1=nombre1,
            nombre2=nombre2,
            apellido1=apellido1,
            apellido2=apellido2,
            phone=phone,
            email=email,
            address=address,
            org=org,
            status='active'
        )

        # Agregar a la base de datos
        db.session.add(new_contact)
        db.session.commit()

        return redirect(url_for('generate_qr', contact_id=new_contact.id))

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
    # Recuperar los datos del contacto desde la base de datos, incluyendo el status
    #cursor = mysql.connection.cursor()
    #cursor.execute("SELECT nombre1, nombre2, apellido1, apellido2, phone, email, address, org, status FROM contacts WHERE id = %s", [contact_id])
    #contact = cursor.fetchone()
    #cursor.close()
    contact = User.query.filter_by(id=contact_id).first()

    if contact is None:
        return "Contacto no encontrado", 404

    nombre1, nombre2, apellido1, apellido2, phone, email, address, org, status = contact

    # Verificar si el contacto está activo
    if status != 'active':
        return "El contacto ya no está disponible.", 403

    # Crear el archivo vCard
    vcard = f"""BEGIN:VCARD
      VERSION:3.0
      N:{apellido2};{nombre2};{apellido1};{nombre1}
      FN:{nombre1} {nombre2} {apellido1} {apellido2}
      TEL;TYPE=WORK,VOICE:+57{phone}
      EMAIL:{email}
      ORG:{org}
      ADR;TYPE=work:;;{address};;;;
      END:VCARD"""

    # Crear la respuesta con el archivo vCard
    response = make_response(vcard)
    response.headers["Content-Disposition"] = f"attachment; filename={nombre1}_{apellido1}.vcf"
    response.headers["Content-Type"] = "text/vcard"

    return response

if __name__ == '__main__':
    app.run(debug=True)
