import os
import json
from pathlib import Path
from datetime import datetime

from dotenv import load_dotenv
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename

load_dotenv(Path(__file__).resolve().parent / '.env')

from models import db, Candidate, Document, DocumentRequest
from resume_parser import parse_resume
from ai_agent import DocumentRequestAgent

app = Flask(__name__)
CORS(app)

app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///candidates.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'resumes'), exist_ok=True)
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'documents'), exist_ok=True)

db.init_app(app)

with app.app_context():
    db.create_all()

ALLOWED_RESUME_EXTENSIONS = {'pdf', 'docx'}
ALLOWED_DOCUMENT_EXTENSIONS = {'pdf', 'jpg', 'jpeg', 'png'}


def allowed_file(filename, allowed_extensions):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions


@app.route('/candidates/upload', methods=['POST'])
def upload_resume():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    if not allowed_file(file.filename, ALLOWED_RESUME_EXTENSIONS):
        return jsonify({'error': 'Invalid file format. Only PDF and DOCX allowed'}), 400

    try:
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_filename = f'{timestamp}_{filename}'
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'resumes', unique_filename)
        file.save(filepath)

        candidate_data, confidence_scores = parse_resume(filepath, filename)

        candidate = Candidate(
            name=candidate_data.get('name'),
            email=candidate_data.get('email'),
            phone=candidate_data.get('phone'),
            company=candidate_data.get('company'),
            designation=candidate_data.get('designation'),
            skills=json.dumps(candidate_data.get('skills', [])),
            confidence_scores=json.dumps(confidence_scores),
            resume_filename=unique_filename,
            extraction_status='completed',
        )

        db.session.add(candidate)
        db.session.commit()

        return jsonify({
            'message': 'Resume uploaded and parsed successfully',
            'candidate': candidate.to_dict(),
        }), 201

    except Exception as e:
        return jsonify({'error': f'Error processing resume: {str(e)}'}), 500


@app.route('/candidates', methods=['GET'])
def get_candidates():
    try:
        candidates = Candidate.query.order_by(Candidate.created_at.desc()).all()
        return jsonify({'candidates': [candidate.to_dict() for candidate in candidates]}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/candidates/<int:id>', methods=['GET'])
def get_candidate(id):
    try:
        candidate = Candidate.query.get_or_404(id)
        return jsonify(candidate.to_dict()), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 404


@app.route('/candidates/<int:id>/request-documents', methods=['POST'])
def request_documents(id):
    try:
        candidate = Candidate.query.get_or_404(id)

        if not candidate.name:
            return jsonify({'error': 'Candidate name is required'}), 400

        agent = DocumentRequestAgent()
        request_message = agent.generate_request({
            'name': candidate.name,
            'email': candidate.email or 'N/A',
            'phone': candidate.phone or 'N/A',
        })

        doc_request = DocumentRequest(
            candidate_id=candidate.id,
            request_message=request_message,
            status='sent',
        )

        db.session.add(doc_request)
        db.session.commit()

        return jsonify({
            'message': 'Document request generated successfully',
            'request': doc_request.to_dict(),
        }), 201

    except Exception as e:
        return jsonify({'error': f'Failed to generate document request: {str(e)}'}), 500


@app.route('/candidates/<int:id>/submit-documents', methods=['POST'])
def submit_documents(id):
    try:
        candidate = Candidate.query.get_or_404(id)

        if 'pan' not in request.files and 'aadhaar' not in request.files:
            return jsonify({'error': 'No documents provided'}), 400

        uploaded_docs = []

        for doc_type in ['pan', 'aadhaar']:
            if doc_type not in request.files:
                continue

            file = request.files[doc_type]
            if file.filename == '':
                continue

            if not allowed_file(file.filename, ALLOWED_DOCUMENT_EXTENSIONS):
                return jsonify({'error': f'Invalid {doc_type} file format'}), 400

            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            unique_filename = f'{doc_type}_{timestamp}_{filename}'
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'documents', unique_filename)
            file.save(filepath)

            document = Document(
                candidate_id=candidate.id,
                document_type=doc_type.upper(),
                filename=unique_filename,
            )
            db.session.add(document)
            uploaded_docs.append(document)

        if uploaded_docs:
            db.session.commit()
            return jsonify({
                'message': 'Documents uploaded successfully',
                'documents': [doc.to_dict() for doc in uploaded_docs],
            }), 201

        return jsonify({'error': 'No valid documents uploaded'}), 400

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/uploads/<path:filename>', methods=['GET'])
def serve_file(filename):
    try:
        if filename.startswith('resumes/') or filename.startswith('documents/'):
            return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
        return jsonify({'error': 'Invalid file path'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 404


@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()}), 200


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5002)
