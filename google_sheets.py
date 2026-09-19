import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import os
import json

class GoogleSheetsManager:
    """Manages Google Sheets integration for donation tracking"""
    
    def __init__(self, credentials_file=None, spreadsheet_id=None):
        """
        Initialize Google Sheets manager
        
        Args:
            credentials_file: Path to Google service account credentials JSON file
            spreadsheet_id: Google Sheets spreadsheet ID
        """
        self.credentials_file = credentials_file or 'google_credentials.json'
        self.spreadsheet_id = spreadsheet_id or '1AwipeokLOKRFZFLaz8lz9c5J-68Wskeo79YfimEncH4'
        self.client = None
        self.spreadsheet = None
        self._connect()
    
    def _connect(self):
        """Connect to Google Sheets"""
        try:
            # Define the scopes
            scopes = [
                'https://www.googleapis.com/auth/spreadsheets',
                'https://www.googleapis.com/auth/drive'
            ]
            
            # Try to load credentials from environment variables first (for deployment)
            creds = None
            if os.getenv('GOOGLE_CREDENTIALS_JSON'):
                try:
                    import json
                    credentials_json = json.loads(os.getenv('GOOGLE_CREDENTIALS_JSON'))
                    creds = Credentials.from_service_account_info(credentials_json, scopes=scopes)
                    print("✅ Loaded Google credentials from environment variables")
                except Exception as e:
                    print(f"⚠️  Error loading credentials from environment: {e}")
            
            # Fallback to credentials file (for local development)
            if not creds and os.path.exists(self.credentials_file):
                creds = Credentials.from_service_account_file(self.credentials_file, scopes=scopes)
                print("✅ Loaded Google credentials from file")
            
            if not creds:
                print(f"⚠️  Google credentials not found")
                print("ℹ️  Google Sheets integration disabled. Using local database only.")
                print("   To enable Google Sheets integration:")
                print("   1. For local development: Create google_credentials.json file")
                print("   2. For deployment: Set GOOGLE_CREDENTIALS_JSON environment variable")
                print("   3. Restart the application")
                return False
            
            self.client = gspread.authorize(creds)
            
            # Open the spreadsheet
            self.spreadsheet = self.client.open_by_key(self.spreadsheet_id)
            print("✅ Connected to Google Sheets successfully")
            return True
            
        except Exception as e:
            print(f"❌ Error connecting to Google Sheets: {e}")
            print("ℹ️  Google Sheets integration disabled. Using local database only.")
            return False
    
    def get_or_create_worksheet(self, worksheet_name):
        """Get existing worksheet or create new one"""
        try:
            if not self.spreadsheet:
                return None
            
            # Try to get existing worksheet
            try:
                worksheet = self.spreadsheet.worksheet(worksheet_name)
                return worksheet
            except gspread.WorksheetNotFound:
                # Create new worksheet
                worksheet = self.spreadsheet.add_worksheet(title=worksheet_name, rows=1000, cols=20)
                
                # Add headers
                headers = [
                    'ID', 'Donor Name', 'Donor Email', 'Donor Phone', 'Amount', 
                    'Currency', 'Purpose', 'Donation Date', 'Payment Method', 
                    'Reference Number', 'Notes', 'Status', 'Created At', 'Created By'
                ]
                worksheet.append_row(headers)
                
                print(f"✅ Created new worksheet: {worksheet_name}")
                return worksheet
                
        except Exception as e:
            print(f"❌ Error getting/creating worksheet {worksheet_name}: {e}")
            return None
    
    def add_donation(self, donation_data, purpose_name):
        """Add a donation record to the appropriate worksheet"""
        try:
            if not self.spreadsheet:
                print("❌ Not connected to Google Sheets")
                return False
            
            # Get or create worksheet for this purpose
            worksheet = self.get_or_create_worksheet(purpose_name)
            if not worksheet:
                return False
            
            # Prepare row data
            row_data = [
                donation_data.get('id', ''),
                donation_data.get('donor_name', ''),
                donation_data.get('donor_email', ''),
                donation_data.get('donor_phone', ''),
                donation_data.get('amount', ''),
                donation_data.get('currency', 'INR'),
                purpose_name,
                donation_data.get('donation_date', ''),
                donation_data.get('payment_method', ''),
                donation_data.get('reference_number', ''),
                donation_data.get('notes', ''),
                'Verified' if donation_data.get('is_verified', False) else 'Pending',
                donation_data.get('created_at', datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
                donation_data.get('created_by', '')
            ]
            
            # Add row to worksheet
            worksheet.append_row(row_data)
            print(f"✅ Added donation to Google Sheets: {purpose_name}")
            return True
            
        except Exception as e:
            print(f"❌ Error adding donation to Google Sheets: {e}")
            return False
    
    def update_donation(self, donation_data, purpose_name, row_index):
        """Update an existing donation record"""
        try:
            if not self.spreadsheet:
                return False
            
            worksheet = self.get_or_create_worksheet(purpose_name)
            if not worksheet:
                return False
            
            # Update the specific row
            row_data = [
                donation_data.get('id', ''),
                donation_data.get('donor_name', ''),
                donation_data.get('donor_email', ''),
                donation_data.get('donor_phone', ''),
                donation_data.get('amount', ''),
                donation_data.get('currency', 'INR'),
                purpose_name,
                donation_data.get('donation_date', ''),
                donation_data.get('payment_method', ''),
                donation_data.get('reference_number', ''),
                donation_data.get('notes', ''),
                'Verified' if donation_data.get('is_verified', False) else 'Pending',
                donation_data.get('created_at', datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
                donation_data.get('created_by', '')
            ]
            
            # Update the row (row_index + 2 because of header row and 1-based indexing)
            worksheet.update(f'A{row_index + 2}:N{row_index + 2}', [row_data])
            print(f"✅ Updated donation in Google Sheets: {purpose_name}")
            return True
            
        except Exception as e:
            print(f"❌ Error updating donation in Google Sheets: {e}")
            return False
    
    def get_donations_summary(self, purpose_name=None):
        """Get summary of donations from Google Sheets"""
        try:
            if not self.spreadsheet:
                return {}
            
            summary = {}
            
            if purpose_name:
                # Get summary for specific purpose
                worksheet = self.get_or_create_worksheet(purpose_name)
                if worksheet:
                    records = worksheet.get_all_records()
                    summary[purpose_name] = {
                        'total_donations': len(records),
                        'total_amount': sum(float(record.get('Amount', 0)) for record in records if record.get('Amount')),
                        'verified_donations': len([r for r in records if r.get('Status') == 'Verified']),
                        'pending_donations': len([r for r in records if r.get('Status') == 'Pending'])
                    }
            else:
                # Get summary for all purposes
                worksheets = self.spreadsheet.worksheets()
                for worksheet in worksheets:
                    if worksheet.title != 'Sheet1':  # Skip default sheet
                        records = worksheet.get_all_records()
                        summary[worksheet.title] = {
                            'total_donations': len(records),
                            'total_amount': sum(float(record.get('Amount', 0)) for record in records if record.get('Amount')),
                            'verified_donations': len([r for r in records if r.get('Status') == 'Verified']),
                            'pending_donations': len([r for r in records if r.get('Status') == 'Pending'])
                        }
            
            return summary
            
        except Exception as e:
            print(f"❌ Error getting donations summary: {e}")
            return {}
    
    def get_all_donations_from_sheets(self):
        """Fetch all donations from Google Sheets and return as list of dictionaries"""
        try:
            if not self.spreadsheet:
                return []
            
            all_donations = []
            worksheets = self.spreadsheet.worksheets()
            
            for worksheet in worksheets:
                if worksheet.title == 'Sheet1':  # Skip default sheet
                    continue
                
                try:
                    records = worksheet.get_all_records()
                    for record in records:
                        # Skip empty rows
                        donor_name = record.get('Donor Name') or record.get('Donors Name', '')
                        amount = record.get('Amount') or record.get('Amount Collected', '')
                        if not donor_name and not amount:
                            continue
                        
                        # Handle different column name formats
                        donor_name = record.get('Donor Name') or record.get('Donors Name', '')
                        amount = record.get('Amount') or record.get('Amount Collected', 0)
                        
                        donation_data = {
                            'id': record.get('Doner_ID', ''),  # Use correct column name
                            'donor_name': donor_name,
                            'donor_email': record.get('Donor Email', ''),
                            'donor_phone': record.get('Donor Phone', ''),
                            'amount': float(amount) if amount else 0,
                            'currency': record.get('Currency', 'INR'),
                            'purpose': worksheet.title,
                            'donation_date': record.get('Donation Date', ''),
                            'payment_method': record.get('Payment Method', 'Cash'),
                            'reference_number': record.get('Reference Number', ''),
                            'notes': record.get('Notes', ''),
                            'status': record.get('Status', 'Verified'),  # Default to verified for existing data
                            'created_at': record.get('Created At', ''),
                            'created_by': record.get('Created By', '')
                        }
                        all_donations.append(donation_data)
                        
                except Exception as e:
                    print(f"⚠️  Error reading worksheet {worksheet.title}: {e}")
                    continue
            
            # Sort by donation date (most recent first)
            all_donations.sort(key=lambda x: x.get('donation_date', ''), reverse=True)
            return all_donations
            
        except Exception as e:
            print(f"❌ Error fetching donations from Google Sheets: {e}")
            return []
    
    def get_donations_by_purpose(self, purpose_name):
        """Fetch donations for a specific purpose from Google Sheets"""
        try:
            if not self.spreadsheet:
                return []
            
            worksheet = self.get_or_create_worksheet(purpose_name)
            if not worksheet:
                return []
            
            records = worksheet.get_all_records()
            donations = []
            
            for record in records:
                # Skip empty rows
                donor_name = record.get('Donor Name') or record.get('Donors Name', '')
                amount = record.get('Amount') or record.get('Amount Collected', '')
                if not donor_name and not amount:
                    continue
                
                # Handle different column name formats
                donor_name = record.get('Donor Name') or record.get('Donors Name', '')
                amount = record.get('Amount') or record.get('Amount Collected', 0)
                
                donation_data = {
                    'id': record.get('ID', ''),
                    'donor_name': donor_name,
                    'donor_email': record.get('Donor Email', ''),
                    'donor_phone': record.get('Donor Phone', ''),
                    'amount': float(amount) if amount else 0,
                    'currency': record.get('Currency', 'INR'),
                    'purpose': purpose_name,
                    'donation_date': record.get('Donation Date', ''),
                    'payment_method': record.get('Payment Method', 'Cash'),
                    'reference_number': record.get('Reference Number', ''),
                    'notes': record.get('Notes', ''),
                    'status': record.get('Status', 'Verified'),  # Default to verified for existing data
                    'created_at': record.get('Created At', ''),
                    'created_by': record.get('Created By', '')
                }
                donations.append(donation_data)
            
            # Sort by donation date (most recent first)
            donations.sort(key=lambda x: x.get('donation_date', ''), reverse=True)
            return donations
            
        except Exception as e:
            print(f"❌ Error fetching donations for purpose {purpose_name}: {e}")
            return []
    
    def sync_donations_from_sheets(self):
        """Sync donations from Google Sheets to local database - COMPLETE REFRESH"""
        try:
            if not self.spreadsheet:
                return False, "Not connected to Google Sheets"
            
            from models import DonationPurpose, OfflineDonation, db
            from datetime import datetime
            
            print("🔄 Starting complete refresh sync...")
            
            # STEP 1: Clear all existing donation data
            print("🗑️  Clearing existing donation data...")
            OfflineDonation.query.delete()
            DonationPurpose.query.delete()
            db.session.commit()
            print("✅ Cleared all existing data")
            
            # STEP 2: Get all donations from Google Sheets
            print("📥 Fetching all data from Google Sheets...")
            all_donations = self.get_all_donations_from_sheets()
            print(f"📊 Found {len(all_donations)} donations in Google Sheets")
            
            synced_count = 0
            purposes_created = set()
            
            # STEP 3: Re-import all data fresh
            for donation_data in all_donations:
                try:
                    # Find or create purpose
                    purpose_name = donation_data['purpose']
                    if purpose_name not in purposes_created:
                        purpose = DonationPurpose(
                            name=purpose_name,
                            description=f"Purpose synced from Google Sheets - {purpose_name}",
                            created_by=1  # Admin user
                        )
                        db.session.add(purpose)
                        db.session.commit()
                        purposes_created.add(purpose_name)
                        print(f"✅ Created purpose: {purpose_name}")
                    else:
                        purpose = DonationPurpose.query.filter_by(name=purpose_name).first()
                    
                    # Create new donation record
                    donor_id = str(donation_data.get('id', '')).strip()
                    worksheet_name = donation_data.get('purpose', '')
                    
                    donation_date = datetime.now().date()
                    if donation_data.get('donation_date'):
                        try:
                            donation_date = datetime.strptime(donation_data['donation_date'], '%Y-%m-%d').date()
                        except ValueError:
                            pass
                    
                    new_donation = OfflineDonation(
                        donor_id=donor_id if donor_id else None,
                        worksheet=worksheet_name,
                        donor_name=donation_data['donor_name'],
                        donor_email=donation_data['donor_email'],
                        donor_phone=donation_data['donor_phone'],
                        amount=donation_data['amount'],
                        currency=donation_data['currency'],
                        purpose_id=purpose.id,
                        donation_date=donation_date,
                        payment_method=donation_data['payment_method'],
                        reference_number=donation_data['reference_number'],
                        notes=donation_data['notes'],
                        is_verified=donation_data['status'] == 'Verified',
                        created_by=1  # Admin user
                    )
                    db.session.add(new_donation)
                    synced_count += 1
                    
                except Exception as e:
                    print(f"⚠️  Error syncing donation: {e}")
                    continue
            
            # STEP 4: Commit all changes
            db.session.commit()
            
            print(f"✅ Complete refresh successful: {synced_count} donations imported")
            return True, f"Complete refresh: {synced_count} donations imported from {len(purposes_created)} worksheets"
            
        except Exception as e:
            db.session.rollback()
            return False, f"Error syncing donations: {e}"
    
    def is_connected(self):
        """Check if Google Sheets is connected"""
        return self.spreadsheet is not None and self.client is not None
    
    def get_sync_statistics(self):
        """Get statistics about the last sync operation"""
        try:
            if not self.spreadsheet:
                return {
                    'connected': False,
                    'worksheets_count': 0,
                    'total_donations_in_sheets': 0,
                    'last_sync': None
                }
            
            worksheets = self.get_available_worksheets()
            total_donations = 0
            
            for worksheet_name in worksheets:
                donations = self.get_donations_by_worksheet(worksheet_name)
                total_donations += len(donations)
            
            return {
                'connected': True,
                'worksheets_count': len(worksheets),
                'total_donations_in_sheets': total_donations,
                'worksheets': worksheets,
                'last_sync': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
        except Exception as e:
            print(f"❌ Error getting sync statistics: {e}")
            return {
                'connected': False,
                'worksheets_count': 0,
                'total_donations_in_sheets': 0,
                'last_sync': None,
                'error': str(e)
            }
    
    def test_connection(self):
        """Test the Google Sheets connection"""
        try:
            if not self.is_connected():
                return False
            
            # Try to access the spreadsheet
            worksheets = self.spreadsheet.worksheets()
            print(f"✅ Connection test successful. Found {len(worksheets)} worksheets.")
            return True
            
        except Exception as e:
            print(f"❌ Connection test failed: {e}")
            return False

    def get_available_worksheets(self):
        """Get list of available worksheets"""
        if not self._connect():
            return []
        
        try:
            worksheets = self.spreadsheet.worksheets()
            # Filter out default 'Sheet1' and return only meaningful worksheet names
            return [ws.title for ws in worksheets if ws.title != 'Sheet1']
        except Exception as e:
            print(f"❌ Error fetching worksheets: {e}")
            return []

    def get_donations_by_worksheet(self, worksheet_name):
        """Get donations from a specific worksheet"""
        if not self._connect():
            return []
        
        try:
            # Find the specific worksheet
            worksheet = None
            for ws in self.spreadsheet.worksheets():
                if ws.title == worksheet_name:
                    worksheet = ws
                    break
            
            if not worksheet:
                print(f"⚠️  Worksheet '{worksheet_name}' not found")
                return []
            
            # Get all records from the worksheet
            records = worksheet.get_all_records()
            donations = []
            
            for record in records:
                # Skip empty rows
                donor_name = record.get('Donor Name') or record.get('Donors Name', '')
                amount = record.get('Amount') or record.get('Amount Collected', '')
                if not donor_name and not amount:
                    continue
                
                # Map the record to our donation format
                donation = {
                    'id': record.get('ID', ''),
                    'donor_name': donor_name,
                    'donor_email': record.get('Donor Email', ''),
                    'donor_phone': record.get('Donor Phone', ''),
                    'amount': float(amount) if amount else 0,
                    'currency': record.get('Currency', 'INR'),
                    'purpose': worksheet.title,
                    'donation_date': record.get('Donation Date', ''),
                    'payment_method': record.get('Payment Method', 'Cash'),
                    'reference_number': record.get('Reference Number', ''),
                    'notes': record.get('Notes', ''),
                    'status': record.get('Status', 'Verified'),
                    'created_at': record.get('Created At', ''),
                    'created_by': record.get('Created By', ''),
                    'worksheet': worksheet.title
                }
                
                donations.append(donation)
            
            # Sort by donation date (most recent first)
            donations.sort(key=lambda x: x.get('donation_date', ''), reverse=True)
            return donations
            
        except Exception as e:
            print(f"❌ Error fetching donations from worksheet '{worksheet_name}': {e}")
            return []

    def get_worksheet_summary(self, worksheet_name):
        """Get summary statistics for a specific worksheet"""
        if not self._connect():
            return {}
        
        try:
            donations = self.get_donations_by_worksheet(worksheet_name)
            
            if not donations:
                return {
                    'total_donations': 0,
                    'total_amount': 0,
                    'verified_donations': 0,
                    'pending_donations': 0,
                    'average_donation': 0
                }
            
            total_amount = sum(donation['amount'] for donation in donations)
            verified_count = len([d for d in donations if d['status'] == 'Verified'])
            pending_count = len([d for d in donations if d['status'] == 'Pending'])
            
            return {
                'total_donations': len(donations),
                'total_amount': total_amount,
                'verified_donations': verified_count,
                'pending_donations': pending_count,
                'average_donation': total_amount / len(donations) if donations else 0
            }
            
        except Exception as e:
            print(f"❌ Error getting summary for worksheet '{worksheet_name}': {e}")
            return {}

# Global instance (lazy initialization)
sheets_manager = None

def get_sheets_manager():
    """Get the sheets manager instance (lazy initialization)"""
    global sheets_manager
    if sheets_manager is None:
        sheets_manager = GoogleSheetsManager()
    return sheets_manager
