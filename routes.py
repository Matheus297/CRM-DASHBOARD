import os
from datetime import datetime, timedelta
from flask import request, jsonify, send_from_directory
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from sqlalchemy import desc, asc
from zoneinfo import ZoneInfo
from app import db
from models import User, Lead, ScheduledMessage, ScheduledContact, MessageTemplate

# Brazil timezone
SAO_PAULO_TZ = ZoneInfo('America/Sao_Paulo')

def register_routes(app):
    
    @app.route('/')
    def home():
        return jsonify({'message': 'API online'})

    @app.route('/api/check-auth')
    def check_auth():
        if current_user.is_authenticated:
            return jsonify({
                'authenticated': True,
                'user': {
                    'id': current_user.id,
                    'username': current_user.username,
                    'email': current_user.email
                }
            })
        return jsonify({'authenticated': False}), 401

    @app.route('/api/login', methods=['POST'])
    def login():
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            return jsonify({
                'message': 'Login realizado com sucesso!',
                'user': {
                    'id': user.id,
                    'username': user.username
                }
            })
        else:
            return jsonify({'error': 'Credenciais inválidas.'}), 401
    
    @app.route('/api/register', methods=['POST'])
    def register():
        data = request.get_json()
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        confirm_password = data.get('confirm_password')
        phone_number = data.get('whatsapp_number', '')
        
        if password != confirm_password:
            return jsonify({'error': 'As senhas não coincidem.'}), 400
        
        if User.query.filter_by(username=username).first():
            return jsonify({'error': 'Nome de usuário já existe.'}), 400
        
        if User.query.filter_by(email=email).first():
            return jsonify({'error': 'Email já cadastrado.'}), 400
        
        user = User(
            username=username,
            email=email,
            phone_number=phone_number
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        return jsonify({'message': 'Conta criada com sucesso!'})
    
    @app.route('/api/logout', methods=['POST'])
    @login_required
    def logout():
        logout_user()
        return jsonify({'message': 'Logout realizado com sucesso!'})
    
    @app.route('/api/dashboard')
    @login_required
    def dashboard():
        total_leads = Lead.query.filter_by(user_id=current_user.id).count()
        leads_frio = Lead.query.filter_by(user_id=current_user.id, status='frio').count()
        leads_quente = Lead.query.filter_by(user_id=current_user.id, status='quente').count()
        leads_fervendo = Lead.query.filter_by(user_id=current_user.id, status='fervendo').count()
        leads_cliente = Lead.query.filter_by(user_id=current_user.id, status='cliente').count()
        
        today = datetime.now(SAO_PAULO_TZ).date()
        upcoming_contacts = ScheduledContact.query.filter(
            ScheduledContact.user_id == current_user.id,
            ScheduledContact.scheduled_time >= today,
            ScheduledContact.is_notified == False
        ).order_by(ScheduledContact.scheduled_time).limit(5).all()
        
        recent_leads = Lead.query.filter_by(user_id=current_user.id).order_by(desc(Lead.created_at)).limit(5).all()
        
        return jsonify({
            'stats': {
                'total': total_leads,
                'frio': leads_frio,
                'quente': leads_quente,
                'fervendo': leads_fervendo,
                'cliente': leads_cliente
            },
            'upcoming_contacts': [{
                'id': c.id,
                'lead_name': c.lead.name,
                'scheduled_time': c.scheduled_time.isoformat(),
                'notes': c.notes
            } for c in upcoming_contacts],
            'recent_leads': [{
                'id': l.id,
                'name': l.name,
                'status': l.status,
                'created_at': l.created_at.isoformat()
            } for l in recent_leads]
        })
    
    @app.route('/api/leads', methods=['GET'])
    @login_required
    def leads():
        status_filter = request.args.get('status', '')
        search_query = request.args.get('search', '')
        
        query = Lead.query.filter_by(user_id=current_user.id)
        
        if status_filter:
            query = query.filter(Lead.status == status_filter)
        
        if search_query:
            query = query.filter(
                (Lead.name.ilike(f'%{search_query}%')) |
                (Lead.phone.ilike(f'%{search_query}%')) |
                (Lead.email.ilike(f'%{search_query}%'))
            )
        
        leads = query.order_by(desc(Lead.updated_at)).all()
        
        return jsonify([{
            'id': l.id,
            'name': l.name,
            'phone': l.phone,
            'email': l.email,
            'status': l.status,
            'notes': l.notes,
            'next_contact_date': l.next_contact_date.isoformat() if l.next_contact_date else None,
            'updated_at': l.updated_at.isoformat()
        } for l in leads])

    @app.route('/api/leads', methods=['POST'])
    @login_required
    def add_lead():
        data = request.get_json()
        name = data.get('name')
        phone = data.get('phone')
        email = data.get('email', '')
        notes = data.get('notes', '')
        next_contact_date = data.get('next_contact_date', '')
        
        next_contact = None
        if next_contact_date:
            try:
                next_contact = datetime.strptime(next_contact_date, '%Y-%m-%d')
            except ValueError:
                return jsonify({'error': 'Data de próximo contato inválida.'}), 400
        
        lead = Lead(
            name=name,
            phone=phone,
            email=email,
            notes=notes,
            next_contact_date=next_contact,
            user_id=current_user.id
        )
        
        db.session.add(lead)
        db.session.commit()
        
        return jsonify({'message': 'Lead adicionado com sucesso!', 'lead': {'id': lead.id}})

    @app.route('/api/leads/<int:lead_id>', methods=['GET'])
    @login_required
    def view_lead(lead_id):
        lead = Lead.query.filter_by(id=lead_id, user_id=current_user.id).first_or_404()
        return jsonify({
            'id': lead.id,
            'name': lead.name,
            'phone': lead.phone,
            'email': lead.email,
            'status': lead.status,
            'notes': lead.notes,
            'next_contact_date': lead.next_contact_date.isoformat() if lead.next_contact_date else None,
            'created_at': lead.created_at.isoformat(),
            'updated_at': lead.updated_at.isoformat()
        })

    @app.route('/api/leads/<int:lead_id>', methods=['PUT'])
    @login_required
    def update_lead(lead_id):
        lead = Lead.query.filter_by(id=lead_id, user_id=current_user.id).first_or_404()
        data = request.get_json()
        
        lead.name = data.get('name', lead.name)
        lead.phone = data.get('phone', lead.phone)
        lead.email = data.get('email', lead.email)
        lead.notes = data.get('notes', lead.notes)
        lead.status = data.get('status', lead.status)
        
        next_contact_date = data.get('next_contact_date', '')
        if next_contact_date:
            try:
                lead.next_contact_date = datetime.strptime(next_contact_date, '%Y-%m-%d')
            except ValueError:
                return jsonify({'error': 'Data inválida'}), 400
        else:
            lead.next_contact_date = None
            
        lead.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({'message': 'Lead atualizado com sucesso!'})

    @app.route('/api/leads/<int:lead_id>', methods=['DELETE'])
    @login_required
    def delete_lead(lead_id):
        lead = Lead.query.filter_by(id=lead_id, user_id=current_user.id).first_or_404()
        
        ScheduledMessage.query.filter_by(lead_id=lead_id).delete()
        ScheduledContact.query.filter_by(lead_id=lead_id).delete()
        
        db.session.delete(lead)
        db.session.commit()
        
        return jsonify({'message': 'Lead removido com sucesso!'})

    @app.route('/api/schedule-contact', methods=['POST'])
    @login_required
    def schedule_contact():
        data = request.get_json()
        lead_id = data.get('lead_id')
        scheduled_time_str = data.get('scheduled_time')
        notes = data.get('notes', '')
        
        if not lead_id or not scheduled_time_str:
            return jsonify({'error': 'Lead e data/hora são obrigatórios.'}), 400
            
        try:
            # Expecting ISO format or similar
            # If coming from datetime-local input, it might be 'YYYY-MM-DDThh:mm'
            scheduled_time = datetime.strptime(scheduled_time_str, '%Y-%m-%dT%H:%M')
        except ValueError:
            try:
                # Try with seconds if present
                scheduled_time = datetime.strptime(scheduled_time_str, '%Y-%m-%dT%H:%M:%S')
            except ValueError:
                return jsonify({'error': 'Formato de data/hora inválido.'}), 400
        
        contact = ScheduledContact(
            lead_id=lead_id,
            scheduled_time=scheduled_time,
            notes=notes,
            user_id=current_user.id
        )
        
        db.session.add(contact)
        db.session.commit()
        
        return jsonify({'message': 'Contato agendado com sucesso!'})

    @app.route('/api/scheduled-contacts', methods=['GET'])
    @login_required
    def get_scheduled_contacts():
        contacts = ScheduledContact.query.filter_by(user_id=current_user.id).order_by(asc(ScheduledContact.scheduled_time)).all()
        return jsonify([{
            'id': c.id,
            'lead_id': c.lead_id,
            'lead_name': c.lead.name,
            'scheduled_time': c.scheduled_time.isoformat(),
            'notes': c.notes,
            'is_notified': c.is_notified
        } for c in contacts])
    @app.route('/api/send-message', methods=['POST'])
    @login_required
    def send_message():
        data = request.get_json()
        lead_id = data.get('lead_id')
        message = data.get('message')
        is_bulk = data.get('is_bulk', False)
        
        if not message:
            return jsonify({'error': 'Mensagem é obrigatória.'}), 400
            
        if is_bulk:
            leads = Lead.query.filter_by(user_id=current_user.id).all()
            for lead in leads:
                # In a real app, this would send an email/SMS/WhatsApp
                # For now, we just create a "sent" scheduled message record
                msg = ScheduledMessage(
                    message=message,
                    scheduled_time=datetime.utcnow(),
                    is_sent=True,
                    user_id=current_user.id,
                    lead_id=lead.id,
                    is_bulk=True
                )
                db.session.add(msg)
        else:
            if not lead_id:
                return jsonify({'error': 'Lead é obrigatório para envio individual.'}), 400
                
            msg = ScheduledMessage(
                message=message,
                scheduled_time=datetime.utcnow(),
                is_sent=True,
                user_id=current_user.id,
                lead_id=lead_id,
                is_bulk=False
            )
            db.session.add(msg)
            
        db.session.commit()
        return jsonify({'message': 'Lembrete enviado com sucesso!'})

    @app.route('/api/schedule-message', methods=['POST'])
    @login_required
    def schedule_message():
        data = request.get_json()
        lead_id = data.get('lead_id')
        message = data.get('message')
        scheduled_time_str = data.get('scheduled_time')
        is_bulk = data.get('is_bulk', False)
        
        if not message or not scheduled_time_str:
            return jsonify({'error': 'Mensagem e data/hora são obrigatórios.'}), 400
            
        try:
            scheduled_time = datetime.strptime(scheduled_time_str, '%Y-%m-%dT%H:%M')
        except ValueError:
            try:
                scheduled_time = datetime.strptime(scheduled_time_str, '%Y-%m-%dT%H:%M:%S')
            except ValueError:
                return jsonify({'error': 'Formato de data/hora inválido.'}), 400
                
        if is_bulk:
            # For bulk scheduling, we might create one record per lead or handle differently
            # Here we create one record per lead for simplicity
            leads = Lead.query.filter_by(user_id=current_user.id).all()
            for lead in leads:
                msg = ScheduledMessage(
                    message=message,
                    scheduled_time=scheduled_time,
                    is_sent=False,
                    user_id=current_user.id,
                    lead_id=lead.id,
                    is_bulk=True
                )
                db.session.add(msg)
        else:
            if not lead_id:
                return jsonify({'error': 'Lead é obrigatório para agendamento individual.'}), 400
                
            msg = ScheduledMessage(
                message=message,
                scheduled_time=scheduled_time,
                is_sent=False,
                user_id=current_user.id,
                lead_id=lead_id,
                is_bulk=False
            )
            db.session.add(msg)
            
        db.session.commit()
        return jsonify({'message': 'Lembrete agendado com sucesso!'})
