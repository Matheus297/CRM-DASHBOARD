import os
from datetime import datetime, timedelta
from flask import render_template, request, redirect, url_for, flash, jsonify, send_from_directory
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from sqlalchemy import desc, asc
import pandas as pd
import pytz
from app import db
from models import User, Lead, ScheduledMessage, ScheduledContact, MessageTemplate

# Brazil timezone
SAO_PAULO_TZ = pytz.timezone('America/Sao_Paulo')

def register_routes(app):
    
    @app.route('/')
    def index():
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
        return redirect(url_for('login'))
    
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            
            user = User.query.filter_by(username=username).first()
            
            if user and user.check_password(password):
                login_user(user)
                flash('Login realizado com sucesso!', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('Credenciais inválidas. Tente novamente.', 'error')
        
        return render_template('login.html')
    
    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if request.method == 'POST':
            username = request.form['username']
            email = request.form['email']
            password = request.form['password']
            confirm_password = request.form['confirm_password']
            phone_number = request.form.get('whatsapp_number', '')
            
            # Validation
            if password != confirm_password:
                flash('As senhas não coincidem.', 'error')
                return render_template('register.html')
            
            if User.query.filter_by(username=username).first():
                flash('Nome de usuário já existe.', 'error')
                return render_template('register.html')
            
            if User.query.filter_by(email=email).first():
                flash('Email já cadastrado.', 'error')
                return render_template('register.html')
            
            # Create new user
            user = User(
                username=username,
                email=email,
                phone_number=phone_number
            )
            user.set_password(password)
            
            db.session.add(user)
            db.session.commit()
            
            flash('Conta criada com sucesso! Faça login para continuar.', 'success')
            return redirect(url_for('login'))
        
        return render_template('register.html')
    
    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        flash('Logout realizado com sucesso!', 'success')
        return redirect(url_for('login'))
    
    @app.route('/dashboard')
    @login_required
    def dashboard():
        # Get lead statistics
        total_leads = Lead.query.filter_by(user_id=current_user.id).count()
        leads_frio = Lead.query.filter_by(user_id=current_user.id, status='frio').count()
        leads_quente = Lead.query.filter_by(user_id=current_user.id, status='quente').count()
        leads_fervendo = Lead.query.filter_by(user_id=current_user.id, status='fervendo').count()
        leads_cliente = Lead.query.filter_by(user_id=current_user.id, status='cliente').count()
        
        # Get upcoming contacts
        today = datetime.now(SAO_PAULO_TZ).date()
        upcoming_contacts = ScheduledContact.query.filter(
            ScheduledContact.user_id == current_user.id,
            ScheduledContact.scheduled_time >= today,
            ScheduledContact.is_notified == False
        ).order_by(ScheduledContact.scheduled_time).limit(5).all()
        
        # Get recent leads
        recent_leads = Lead.query.filter_by(user_id=current_user.id).order_by(desc(Lead.created_at)).limit(5).all()
        
        return render_template('dashboard.html', 
                             total_leads=total_leads,
                             leads_frio=leads_frio,
                             leads_quente=leads_quente,
                             leads_fervendo=leads_fervendo,
                             leads_cliente=leads_cliente,
                             upcoming_contacts=upcoming_contacts,
                             recent_leads=recent_leads)
    
    @app.route('/leads')
    @login_required
    def leads():
        # Get filter parameters
        status_filter = request.args.get('status', '')
        search_query = request.args.get('search', '')
        
        # Build query
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
        
        return render_template('leads.html', leads=leads, status_filter=status_filter, search_query=search_query)
    
    @app.route('/leads/add', methods=['GET', 'POST'])
    @login_required
    def add_lead():
        if request.method == 'POST':
            name = request.form['name']
            phone = request.form['phone']
            email = request.form.get('email', '')
            notes = request.form.get('notes', '')
            next_contact_date = request.form.get('next_contact_date', '')
            
            # Parse next contact date
            next_contact = None
            if next_contact_date:
                try:
                    next_contact = datetime.strptime(next_contact_date, '%Y-%m-%d')
                except ValueError:
                    flash('Data de próximo contato inválida.', 'error')
                    return render_template('lead_form.html')
            
            # Create new lead
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
            
            flash('Lead adicionado com sucesso!', 'success')
            return redirect(url_for('leads'))
        
        return render_template('lead_form.html')
    
    @app.route('/leads/<int:lead_id>')
    @login_required
    def view_lead(lead_id):
        lead = Lead.query.filter_by(id=lead_id, user_id=current_user.id).first_or_404()
        return render_template('lead_detail.html', lead=lead)
    
    @app.route('/leads/<int:lead_id>/edit', methods=['GET', 'POST'])
    @login_required
    def edit_lead(lead_id):
        lead = Lead.query.filter_by(id=lead_id, user_id=current_user.id).first_or_404()
        
        if request.method == 'POST':
            lead.name = request.form['name']
            lead.phone = request.form['phone']
            lead.email = request.form.get('email', '')
            lead.notes = request.form.get('notes', '')
            lead.status = request.form.get('status', 'frio')
            
            next_contact_date = request.form.get('next_contact_date', '')
            if next_contact_date:
                try:
                    lead.next_contact_date = datetime.strptime(next_contact_date, '%Y-%m-%d')
                except ValueError:
                    flash('Data de próximo contato inválida.', 'error')
                    return render_template('lead_form.html', lead=lead)
            else:
                lead.next_contact_date = None
            
            lead.updated_at = datetime.utcnow()
            db.session.commit()
            
            flash('Lead atualizado com sucesso!', 'success')
            return redirect(url_for('view_lead', lead_id=lead.id))
        
        return render_template('lead_form.html', lead=lead)
    
    @app.route('/leads/<int:lead_id>/delete', methods=['POST'])
    @login_required
    def delete_lead(lead_id):
        lead = Lead.query.filter_by(id=lead_id, user_id=current_user.id).first_or_404()
        
        # Delete related scheduled messages and contacts
        ScheduledMessage.query.filter_by(lead_id=lead_id).delete()
        ScheduledContact.query.filter_by(lead_id=lead_id).delete()
        
        db.session.delete(lead)
        db.session.commit()
        
        flash('Lead removido com sucesso!', 'success')
        return redirect(url_for('leads'))
    
    @app.route('/leads/<int:lead_id>/advance_status', methods=['POST'])
    @login_required
    def advance_lead_status(lead_id):
        lead = Lead.query.filter_by(id=lead_id, user_id=current_user.id).first_or_404()
        
        status_progression = {
            'frio': 'quente',
            'quente': 'fervendo',
            'fervendo': 'cliente'
        }
        
        if lead.status in status_progression:
            lead.status = status_progression[lead.status]
            lead.updated_at = datetime.utcnow()
            db.session.commit()
            flash(f'Status do lead alterado para {lead.status}!', 'success')
        
        return redirect(url_for('view_lead', lead_id=lead.id))
    
    @app.route('/leads/import', methods=['GET', 'POST'])
    @login_required
    def import_leads():
        if request.method == 'POST':
            if 'file' not in request.files:
                flash('Nenhum arquivo selecionado.', 'error')
                return redirect(request.url)
            
            file = request.files['file']
            if file.filename == '':
                flash('Nenhum arquivo selecionado.', 'error')
                return redirect(request.url)
            
            if file and file.filename.endswith(('.xlsx', '.xls')):
                try:
                    # Read Excel file
                    df = pd.read_excel(file)
                    
                    # Check required columns
                    required_columns = ['nome', 'telefone']
                    missing_columns = [col for col in required_columns if col not in df.columns]
                    
                    if missing_columns:
                        flash(f'Colunas obrigatórias não encontradas: {", ".join(missing_columns)}', 'error')
                        return redirect(request.url)
                    
                    # Import leads
                    imported_count = 0
                    for index, row in df.iterrows():
                        try:
                            lead = Lead(
                                name=str(row['nome']),
                                phone=str(row['telefone']),
                                email=str(row.get('email', '')),
                                notes=str(row.get('observacoes', '')),
                                user_id=current_user.id
                            )
                            db.session.add(lead)
                            imported_count += 1
                        except Exception as e:
                            print(f"Erro ao importar linha {index + 1}: {str(e)}")
                            continue
                    
                    db.session.commit()
                    flash(f'{imported_count} leads importados com sucesso!', 'success')
                    return redirect(url_for('leads'))
                    
                except Exception as e:
                    flash(f'Erro ao processar arquivo: {str(e)}', 'error')
                    return redirect(request.url)
            else:
                flash('Apenas arquivos Excel (.xlsx, .xls) são aceitos.', 'error')
                return redirect(request.url)
        
        return render_template('import_leads.html')
    
    @app.route('/templates')
    @login_required
    def message_templates():
        templates = MessageTemplate.query.filter_by(user_id=current_user.id).order_by(desc(MessageTemplate.created_at)).all()
        return render_template('message_templates.html', templates=templates)
    
    @app.route('/templates/add', methods=['GET', 'POST'])
    @login_required
    def add_template():
        if request.method == 'POST':
            name = request.form['name']
            content = request.form['content']
            
            template = MessageTemplate(
                name=name,
                content=content,
                user_id=current_user.id
            )
            
            db.session.add(template)
            db.session.commit()
            
            flash('Template criado com sucesso!', 'success')
            return redirect(url_for('message_templates'))
        
        return render_template('template_form.html')
    
    @app.route('/templates/<int:template_id>/edit', methods=['GET', 'POST'])
    @login_required
    def edit_template(template_id):
        template = MessageTemplate.query.filter_by(id=template_id, user_id=current_user.id).first_or_404()
        
        if request.method == 'POST':
            template.name = request.form['name']
            template.content = request.form['content']
            template.updated_at = datetime.utcnow()
            
            db.session.commit()
            
            flash('Template atualizado com sucesso!', 'success')
            return redirect(url_for('message_templates'))
        
        return render_template('template_form.html', template=template)
    
    @app.route('/templates/<int:template_id>/delete', methods=['POST'])
    @login_required
    def delete_template(template_id):
        template = MessageTemplate.query.filter_by(id=template_id, user_id=current_user.id).first_or_404()
        
        db.session.delete(template)
        db.session.commit()
        
        flash('Template removido com sucesso!', 'success')
        return redirect(url_for('message_templates'))
    
    @app.route('/scheduled-contacts')
    @login_required
    def scheduled_contacts():
        contacts = ScheduledContact.query.filter_by(user_id=current_user.id).order_by(asc(ScheduledContact.scheduled_time)).all()
        return render_template('scheduled_contacts.html', contacts=contacts)
    
    @app.route('/schedule-contact', methods=['GET', 'POST'])
    @login_required
    def schedule_contact():
        if request.method == 'POST':
            lead_id = request.form['lead_id']
            scheduled_date = request.form['scheduled_date']
            scheduled_time = request.form['scheduled_time']
            notes = request.form.get('notes', '')
            
            # Combine date and time
            try:
                scheduled_datetime = datetime.strptime(f"{scheduled_date} {scheduled_time}", '%Y-%m-%d %H:%M')
            except ValueError:
                flash('Data e hora inválidas.', 'error')
                leads = Lead.query.filter_by(user_id=current_user.id).all()
                return render_template('contact_schedule_form.html', leads=leads)
            
            # Create scheduled contact
            contact = ScheduledContact(
                lead_id=lead_id,
                scheduled_time=scheduled_datetime,
                notes=notes,
                user_id=current_user.id
            )
            
            db.session.add(contact)
            db.session.commit()
            
            flash('Contato agendado com sucesso!', 'success')
            return redirect(url_for('scheduled_contacts'))
        
        leads = Lead.query.filter_by(user_id=current_user.id).all()
        return render_template('contact_schedule_form.html', leads=leads)
    
    @app.route('/scheduled-contacts/<int:contact_id>/delete', methods=['POST'])
    @login_required
    def delete_scheduled_contact(contact_id):
        contact = ScheduledContact.query.filter_by(id=contact_id, user_id=current_user.id).first_or_404()
        
        db.session.delete(contact)
        db.session.commit()
        
        flash('Contato agendado removido com sucesso!', 'success')
        return redirect(url_for('scheduled_contacts'))
    
    @app.route('/whatsapp-bulk')
    @login_required
    def whatsapp_bulk():
        leads = Lead.query.filter_by(user_id=current_user.id).all()
        templates = MessageTemplate.query.filter_by(user_id=current_user.id).all()
        return render_template('whatsapp_bulk_send.html', leads=leads, templates=templates)
    
    @app.route('/whatsapp/send/<int:lead_id>')
    @login_required
    def whatsapp_send(lead_id):
        lead = Lead.query.filter_by(id=lead_id, user_id=current_user.id).first_or_404()
        templates = MessageTemplate.query.filter_by(user_id=current_user.id).all()
        return render_template('whatsapp_send.html', lead=lead, templates=templates)
    
    @app.route('/settings')
    @login_required
    def settings():
        return render_template('settings.html', user=current_user)