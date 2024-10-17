from flask import Flask, render_template, request, redirect, url_for, send_file, make_response
import qrcode
from io import BytesIO
from flask_mysqldb import MySQL

app = Flask(__name__)

# Configuración de la base de datos MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'contact_db'

mysql = MySQL(app)

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
        cursor = mysql.connection.cursor()
        cursor.execute("""
            INSERT INTO contacts (nombre1, nombre2, apellido1, apellido2, phone, email, address, org, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'active')
        """, (nombre1, nombre2, apellido1, apellido2, phone, email, address, org))
        mysql.connection.commit()
        contact_id = cursor.lastrowid
        cursor.close()

        return redirect(url_for('generate_qr', contact_id=contact_id))

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
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT nombre1, nombre2, apellido1, apellido2, phone, email, address, org, status FROM contacts WHERE id = %s", [contact_id])
    contact = cursor.fetchone()
    cursor.close()

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
