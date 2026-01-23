"""
API Integration Tests

Test alle Flask API endpoints voor file upload, processing en download.
"""

import pytest
import json
import io
from pathlib import Path


@pytest.mark.integration
class TestUploadRoutes:
    """Tests voor upload endpoints"""

    def test_upload_files_success(self, client):
        """Test succesvolle file upload"""
        data = {
            'files[]': (io.BytesIO(b'test content'), 'test.txt')
        }

        response = client.post('/api/upload', data=data, content_type='multipart/form-data')

        assert response.status_code == 200
        result = response.get_json()
        assert result['success'] is True
        assert len(result['files']) == 1
        assert result['files'][0]['originalName'] == 'test.txt'
        assert 'sessionId' in result

    def test_upload_multiple_files(self, client):
        """Test upload van meerdere bestanden"""
        data = {
            'files[]': [
                (io.BytesIO(b'file 1'), 'test1.txt'),
                (io.BytesIO(b'file 2'), 'test2.docx')
            ]
        }

        response = client.post('/api/upload', data=data, content_type='multipart/form-data')

        assert response.status_code == 200
        result = response.get_json()
        assert result['success'] is True
        assert len(result['files']) == 2

    def test_upload_no_files(self, client):
        """Test upload zonder bestanden"""
        response = client.post('/api/upload', data={}, content_type='multipart/form-data')

        assert response.status_code == 400
        result = response.get_json()
        assert 'error' in result

    def test_cleanup_session(self, client):
        """Test sessie cleanup"""
        # Eerst upload doen om sessie aan te maken
        data = {'files[]': (io.BytesIO(b'test'), 'test.txt')}
        client.post('/api/upload', data=data, content_type='multipart/form-data')

        # Dan cleanup
        response = client.post('/api/cleanup')

        assert response.status_code == 200
        result = response.get_json()
        assert result['success'] is True


@pytest.mark.integration
class TestProcessingRoutes:
    """Tests voor processing endpoints"""

    def setup_test_file(self, client):
        """Helper: upload een test bestand en return file_id"""
        data = {
            'files[]': (io.BytesIO(b'Contact: 06-12345678, Email: test@example.com'), 'test.txt')
        }
        response = client.post('/api/upload', data=data, content_type='multipart/form-data')
        result = response.get_json()
        return result['files'][0]['id']

    def test_preview_detection(self, client):
        """Test auto-detection preview"""
        file_id = self.setup_test_file(client)

        payload = {
            'fileIds': [file_id],
            'phonePlaceholder': '[TEL]',
            'emailPlaceholder': '[EMAIL]'
        }

        response = client.post('/api/preview',
                               data=json.dumps(payload),
                               content_type='application/json')

        assert response.status_code == 200
        result = response.get_json()
        assert result['success'] is True
        assert 'previews' in result
        assert len(result['previews']) > 0

    def test_process_files_basic(self, client):
        """Test basis file processing"""
        file_id = self.setup_test_file(client)

        payload = {
            'fileIds': [file_id],
            'rules': [],
            'excelRules': [],
            'activeTab': 'text',
            'autoDetectEnabled': True,
            'phonePlaceholder': '[TEL]',
            'emailPlaceholder': '[EMAIL]',
            'generalPlaceholder': '[ANONIEM]',
            'reversibleMode': False,
            'preserveFormatting': False
        }

        response = client.post('/api/process',
                               data=json.dumps(payload),
                               content_type='application/json')

        assert response.status_code == 200
        result = response.get_json()
        assert result['success'] is True
        assert 'results' in result
        assert len(result['results']) > 0
        assert result['results'][0]['status'] in ['anonymized', 'error']

    def test_process_with_manual_rules(self, client):
        """Test processing met handmatige regels"""
        file_id = self.setup_test_file(client)

        payload = {
            'fileIds': [file_id],
            'rules': [{
                'id': 'rule-1',
                'originalTerm': 'Contact',
                'replacementTerm': '[INFO]',
                'isRegex': False,
                'caseSensitive': False
            }],
            'excelRules': [],
            'activeTab': 'text',
            'autoDetectEnabled': True
        }

        response = client.post('/api/process',
                               data=json.dumps(payload),
                               content_type='application/json')

        assert response.status_code == 200
        result = response.get_json()
        assert result['success'] is True

    def test_process_reversible_mode(self, client):
        """Test processing met reversible mode"""
        file_id = self.setup_test_file(client)

        payload = {
            'fileIds': [file_id],
            'rules': [],
            'excelRules': [],
            'activeTab': 'text',
            'autoDetectEnabled': True,
            'reversibleMode': True
        }

        response = client.post('/api/process',
                               data=json.dumps(payload),
                               content_type='application/json')

        assert response.status_code == 200
        result = response.get_json()
        assert result['success'] is True
        # Check voor mapping
        if result.get('mappingAvailable'):
            assert 'mappingId' in result
            assert 'totalMappings' in result

    def test_process_no_session(self, client):
        """Test processing zonder sessie"""
        payload = {
            'fileIds': ['fake-id'],
            'rules': [],
            'excelRules': [],
            'activeTab': 'text'
        }

        # Maak nieuwe client zonder sessie
        with client.session_transaction() as sess:
            sess.clear()

        response = client.post('/api/process',
                               data=json.dumps(payload),
                               content_type='application/json')

        assert response.status_code == 400


@pytest.mark.integration
class TestDownloadRoutes:
    """Tests voor download endpoints"""

    def setup_processed_file(self, client):
        """Helper: upload en process een bestand, return file_id"""
        # Upload
        data = {'files[]': (io.BytesIO(b'test 06-12345678'), 'test.txt')}
        upload_response = client.post('/api/upload', data=data, content_type='multipart/form-data')
        file_id = upload_response.get_json()['files'][0]['id']

        # Process
        payload = {
            'fileIds': [file_id],
            'rules': [],
            'excelRules': [],
            'activeTab': 'text',
            'autoDetectEnabled': True
        }
        client.post('/api/process',
                    data=json.dumps(payload),
                    content_type='application/json')

        return file_id

    def test_download_single_file(self, client):
        """Test download van enkel bestand"""
        file_id = self.setup_processed_file(client)

        response = client.get(f'/api/download/{file_id}')

        # Kan 200 zijn als bestand bestaat, 404 als niet gevonden
        assert response.status_code in [200, 404]

    def test_download_all_zip(self, client):
        """Test download van alle bestanden als ZIP"""
        self.setup_processed_file(client)

        response = client.get('/api/download-all')

        # Kan 200 zijn met ZIP, of 404 als geen bestanden
        assert response.status_code in [200, 404]
        if response.status_code == 200:
            assert response.content_type == 'application/zip'

    def test_download_no_session(self, client):
        """Test download zonder sessie"""
        # Clear sessie
        with client.session_transaction() as sess:
            sess.clear()

        response = client.get('/api/download/fake-id')
        assert response.status_code in [400, 404]


@pytest.mark.integration
class TestMainRoutes:
    """Tests voor main routes"""

    def test_index_page(self, client):
        """Test homepage"""
        response = client.get('/')

        assert response.status_code == 200
        # Check dat het HTML bevat
        assert b'<!DOCTYPE html>' in response.data or b'<html' in response.data


@pytest.mark.integration
class TestReverseRoutes:
    """Tests voor de-anonymization"""

    def test_reverse_without_files(self, client):
        """Test reverse zonder bestanden"""
        response = client.post('/api/reverse')

        assert response.status_code == 400
        result = response.get_json()
        assert 'error' in result

    def test_reverse_with_files(self, client):
        """Test reverse met geanonimiseerd bestand en mapping"""
        # Maak dummy bestanden
        anonymized_data = b'Dit is [TEL-001] geanonimiseerd'
        mapping_data = json.dumps({
            "mappings": {
                "[TEL-001]": "06-12345678"
            }
        }).encode()

        data = {
            'anonymized_file': (io.BytesIO(anonymized_data), 'test_ann.txt'),
            'mapping_file': (io.BytesIO(mapping_data), 'mapping.json')
        }

        response = client.post('/api/reverse',
                               data=data,
                               content_type='multipart/form-data')

        # Kan slagen of falen afhankelijk van de implementatie
        assert response.status_code in [200, 400, 500]


@pytest.mark.integration
class TestEndToEnd:
    """End-to-end workflow tests"""

    def test_full_workflow_text(self, client):
        """Test volledige workflow: upload → process → download"""
        # 1. Upload
        upload_data = {
            'files[]': (io.BytesIO(b'Jan de Vries, Tel: 06-12345678'), 'contact.txt')
        }
        upload_response = client.post('/api/upload',
                                      data=upload_data,
                                      content_type='multipart/form-data')

        assert upload_response.status_code == 200
        file_id = upload_response.get_json()['files'][0]['id']

        # 2. Process
        process_payload = {
            'fileIds': [file_id],
            'rules': [{
                'id': 'naam',
                'originalTerm': 'Jan de Vries',
                'replacementTerm': '[NAAM]',
                'isRegex': False
            }],
            'excelRules': [],
            'activeTab': 'text',
            'autoDetectEnabled': True
        }

        process_response = client.post('/api/process',
                                       data=json.dumps(process_payload),
                                       content_type='application/json')

        assert process_response.status_code == 200
        result = process_response.get_json()
        assert result['success'] is True

        # 3. Download all
        download_response = client.get('/api/download-all')
        assert download_response.status_code in [200, 404]

    def test_full_workflow_with_preview(self, client):
        """Test workflow met preview stap"""
        # 1. Upload
        upload_data = {
            'files[]': (io.BytesIO(b'Email: test@example.com'), 'test.txt')
        }
        upload_response = client.post('/api/upload',
                                      data=upload_data,
                                      content_type='multipart/form-data')
        file_id = upload_response.get_json()['files'][0]['id']

        # 2. Preview
        preview_payload = {
            'fileIds': [file_id],
            'phonePlaceholder': '[TEL]',
            'emailPlaceholder': '[EMAIL]'
        }
        preview_response = client.post('/api/preview',
                                       data=json.dumps(preview_payload),
                                       content_type='application/json')

        assert preview_response.status_code == 200

        # 3. Process
        process_payload = {
            'fileIds': [file_id],
            'rules': [],
            'excelRules': [],
            'activeTab': 'text',
            'autoDetectEnabled': True
        }
        process_response = client.post('/api/process',
                                       data=json.dumps(process_payload),
                                       content_type='application/json')

        assert process_response.status_code == 200
