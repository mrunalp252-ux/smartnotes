import unittest
import os
from app import app, db, Note

class SmartNotesTestCase(unittest.TestCase):
    def setUp(self):
        # Configure app for testing
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['WTF_CSRF_ENABLED'] = False
        self.client = app.test_client()

        with app.app_context():
            db.create_all()

    def tearDown(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()

    def test_dashboard_redirect_and_empty(self):
        """Test root redirects to /notes and dashboard renders successfully"""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 302)
        self.assertIn('/notes', response.headers['Location'])

        dash_res = self.client.get('/notes')
        self.assertEqual(dash_res.status_code, 200)
        self.assertIn(b'SmartNotes', dash_res.data)
        self.assertIn(b'No notes found', dash_res.data)

    def test_create_note_success(self):
        """Test note creation with valid data"""
        response = self.client.post('/notes/new', data={
            'title': 'Test Algorithms',
            'content': 'Studying Binary Search Trees and Big-O notation.',
            'category': 'Programming',
            'is_pinned': '1'
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Test Algorithms', response.data)
        self.assertIn(b'Note created successfully!', response.data)
        self.assertIn(b'Pinned', response.data)

    def test_create_note_validation_failures(self):
        """Test validation when title or content is empty"""
        # Empty title
        res1 = self.client.post('/notes/new', data={
            'title': '   ',
            'content': 'Some content',
            'category': 'College'
        })
        self.assertEqual(res1.status_code, 400)
        self.assertIn(b'Note title is required.', res1.data)

        # Empty content
        res2 = self.client.post('/notes/new', data={
            'title': 'Valid Title',
            'content': '   ',
            'category': 'College'
        })
        self.assertEqual(res2.status_code, 400)
        self.assertIn(b'Note content is required.', res2.data)

    def test_edit_note(self):
        """Test editing an existing note"""
        with app.app_context():
            note = Note(title='Old Title', content='Old Content', category='College', is_pinned=False)
            db.session.add(note)
            db.session.commit()
            note_id = note.id

        # GET edit page
        get_res = self.client.get(f'/notes/{note_id}/edit')
        self.assertEqual(get_res.status_code, 200)
        self.assertIn(b'Old Title', get_res.data)

        # POST edit
        post_res = self.client.post(f'/notes/{note_id}/edit', data={
            'title': 'Updated Title',
            'content': 'Updated Content with extra details.',
            'category': 'Projects',
            'is_pinned': '1'
        }, follow_redirects=True)

        self.assertEqual(post_res.status_code, 200)
        self.assertIn(b'Updated Title', post_res.data)
        self.assertIn(b'Note updated successfully!', post_res.data)

    def test_toggle_pin(self):
        """Test pinning and unpinning notes"""
        with app.app_context():
            note = Note(title='Pin Test', content='Content', category='Ideas', is_pinned=False)
            db.session.add(note)
            db.session.commit()
            note_id = note.id

        # AJAX toggle pin
        ajax_res = self.client.post(f'/notes/{note_id}/toggle-pin', headers={'X-Requested-With': 'XMLHttpRequest'})
        self.assertEqual(ajax_res.status_code, 200)
        self.assertTrue(ajax_res.json['is_pinned'])

        # Standard toggle pin
        std_res = self.client.post(f'/notes/{note_id}/toggle-pin', follow_redirects=True)
        self.assertEqual(std_res.status_code, 200)
        self.assertIn(b'Note unpinned successfully!', std_res.data)

    def test_search_and_filter(self):
        """Test searching and filtering by category"""
        with app.app_context():
            n1 = Note(title='Python Flask Guide', content='Microframework notes', category='Programming')
            n2 = Note(title='Exam Preparation', content='Semester exams revision', category='College')
            db.session.add_all([n1, n2])
            db.session.commit()

        # Search for Flask
        res = self.client.get('/notes?q=Flask')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Python Flask Guide', res.data)
        self.assertNotIn(b'Exam Preparation', res.data)

        # Search with no match
        empty_res = self.client.get('/notes?q=NonExistentKeywordXYZ')
        self.assertEqual(empty_res.status_code, 200)
        self.assertIn(b'No notes found', empty_res.data)

        # Category filter
        cat_res = self.client.get('/notes?category=College')
        self.assertEqual(cat_res.status_code, 200)
        self.assertIn(b'Exam Preparation', cat_res.data)
        self.assertNotIn(b'Python Flask Guide', cat_res.data)

    def test_seed_sample_notes(self):
        """Test seeding sample notes for college demonstration"""
        response = self.client.post('/seed-sample-notes', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Sample notes populated successfully', response.data)
        self.assertIn(b'Java DSA', response.data)
        self.assertIn(b'College Project Ideas', response.data)
        self.assertIn(b'Python Flask', response.data)
        self.assertIn(b'Exam Preparation', response.data)

    def test_delete_note(self):
        """Test deleting a note"""
        with app.app_context():
            note = Note(title='Delete Me', content='Temporary note', category='Other')
            db.session.add(note)
            db.session.commit()
            note_id = note.id

        del_res = self.client.post(f'/notes/{note_id}/delete', follow_redirects=True)
        self.assertEqual(del_res.status_code, 200)
        self.assertIn(b'Note deleted successfully!', del_res.data)
        self.assertNotIn(b'Delete Me', del_res.data)

    def test_invalid_note_id_graceful_handling(self):
        """Test editing or deleting non-existent note ID handles gracefully"""
        edit_res = self.client.get('/notes/99999/edit', follow_redirects=True)
        self.assertEqual(edit_res.status_code, 200)
        self.assertIn(b'Note not found', edit_res.data)

        del_res = self.client.post('/notes/99999/delete', follow_redirects=True)
        self.assertEqual(del_res.status_code, 200)
        self.assertIn(b'Note not found', del_res.data)

if __name__ == '__main__':
    unittest.main()
