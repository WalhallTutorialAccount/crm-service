from datetime import datetime

from flask import current_app as app, request, abort, g
from flask_restplus import Api, Resource, fields, inputs
from sqlalchemy import or_, and_
from .models import db, Contact, Appointment
from .auth import auth_required

api = Api(
    doc='/docs/',
    title='Service API'
)


@api.route('/health_check/', doc=False)
class Health(Resource):

    def get(self):
        is_database_working, output = True, 'database is ok'
        try:
            db.engine.execute('SELECT 1')
        except Exception as e:
            is_database_working, output = False, str(e)

        return {'status': is_database_working, 'output': output}


@api.route('/docs/swagger.json', doc=False)
class Swagger(Resource):
    """
    Flask-Restplus has hardcoded "/swagger.json" URL, but we need to expose it as "/docs/swagger.json"
    """

    def get(self):
        return app.view_functions['specs']()


# Define your own resources here
contact = api.model('Contact', {
    'uuid': fields.String(readonly=True, description='UUID'),
    'first_name': fields.String(required=True, description='First Name'),
    'last_name': fields.String(required=True, description='Last Name'),
    'company': fields.String(required=False, description='Company'),
    'address': fields.String(required=True, description='Address'),
    'phone': fields.String(required=False, description='Phone'),
    'email': fields.String(required=False, description='Email'),
})

@api.route('/contact/')
class ContactList(Resource):

    @auth_required
    @api.marshal_with(contact, as_list=True)
    def get(self):
        return Contact.query.all()

    @auth_required
    @api.marshal_with(contact)
    @api.expect(contact, validate=True)
    def post(self):
        kwargs = request.json
        contact = Contact(**kwargs)
        db.session.add(contact)
        db.session.commit()
        return contact, 201

@api.route('/contact/<string:contact_uuid>/')
class ContactDetail(Resource):

    @auth_required
    @api.marshal_with(contact, as_list=True)
    def get(self, contact_uuid):
        contact = Contact.query.get_or_404(contact_uuid)
        return contact

    @auth_required
    @api.marshal_with(contact, as_list=True)
    def put(self, contact_uuid):
        contact = Contact.query.get_or_404(contact_uuid)
        kwargs = request.json
        contact.first_name = kwargs.get('first_name')
        contact.last_name = kwargs.get('last_name')
        contact.company = kwargs.get('company')
        contact.address = kwargs.get('address')
        contact.phone = kwargs.get('phone')
        contact.email = kwargs.get('email')
        db.session.commit()
        return contact, 200

    @auth_required
    def delete(self, contact_uuid):
        contact = Contact.query.get_or_404(contact_uuid)
        db.session.delete(contact)
        db.session.commit()
        return '', 204

appointment = api.model('Appointment', {
    'uuid': fields.String(readonly=True, description='UUID'),
    'name': fields.String(required=True, description='Name'),
    'start_date': fields.DateTime(required=True, description='Start date'),
    'end_date': fields.DateTime(required=True, description='End date'),
    'organization_uuid': fields.String(readonly=True, description='Organization UUID'),
    'contact_uuid': fields.String(required=True, description='Contact UUID'),
    'contact': fields.Nested(contact, readonly=True, description='Contact')
})

appointment_parser = api.parser()
appointment_parser.add_argument('date', type=inputs.date_from_iso8601, help='Date', location='args')

@api.route('/appointment/')
class AppointmentList(Resource):

    @auth_required
    @api.marshal_with(appointment, as_list=True)
    def get(self):
        query = Appointment.query
        args = appointment_parser.parse_args()
        if args.get('date'):
            date = args['date']
            day_start = datetime(date.year, date.month, date.day, 0, 0, 0)
            day_end = datetime(date.year, date.month, date.day, 23, 59, 59)
            query = query.filter(or_(
                and_(Appointment.start_date <= day_start, day_start <= Appointment.end_date),
                and_(day_start <= Appointment.start_date, Appointment.start_date <= day_end)
            ))

        if 'organization_uuid' in g:
            query = query.filter_by(organization_uuid=g.get('organization_uuid'))

        return query.all()

    @auth_required
    @api.marshal_with(appointment)
    @api.expect(appointment, validate=True)
    def post(self):
        kwargs = request.json
        appointment = Appointment(**kwargs)
        appointment.organization_uuid = g.get('organization_uuid')
        db.session.add(appointment)
        db.session.commit()
        return appointment, 201

@api.route('/appointment/<string:appointment_uuid>/')
class AppointmentDetail(Resource):

    @auth_required
    @api.marshal_with(appointment, as_list=True)
    def get(self, appointment_uuid):
        appointment = Appointment.query.get_or_404(appointment_uuid)
        return appointment

    @auth_required
    @api.marshal_with(appointment, as_list=True)
    def put(self, appointment_uuid):
        appointment = Appointment.query.get_or_404(appointment_uuid)
        kwargs = request.json
        appointment.name = kwargs.get('name')
        appointment.start_date = kwargs.get('start_date')
        appointment.end_date = kwargs.get('end_date')
        appointment.contact_uuid = kwargs.get('contact_uuid')
        db.session.commit()
        return appointment, 200

    @auth_required
    def delete(self, appointment_uuid):
        appointment = Appointment.query.get_or_404(appointment_uuid)
        if 'organization_uuid' in g and not appointment.organization_uuid == g.get('organization_uuid'):
            abort(404)
        db.session.delete(appointment)
        db.session.commit()
        return '', 204