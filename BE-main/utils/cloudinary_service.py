import cloudinary
import cloudinary.uploader
import cloudinary.api
import os
from werkzeug.utils import secure_filename
import uuid
from datetime import datetime
import json

class CloudinaryService:
    def __init__(self):
        # Configure Cloudinary
        self.cloud_name = os.getenv('CLOUD_NAME')
        self.api_key = os.getenv('CLOUD_API_KEY')
        self.api_secret = os.getenv('CLOUD_API_SECRET')
        
        # Check if Cloudinary is properly configured
        self.is_configured = bool(self.cloud_name and self.api_key and self.api_secret)
        
        if self.is_configured:
            cloudinary.config(
                cloud_name=self.cloud_name,
                api_key=self.api_key,
                api_secret=self.api_secret
            )
        else:
            print("⚠️ Cloudinary not configured. Using development mode for file attachments.")
        
        # Allowed file extensions
        self.allowed_extensions = {
            'images': {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'},
            'documents': {'pdf', 'doc', 'docx', 'txt', 'rtf'},
            'spreadsheets': {'xls', 'xlsx', 'csv'},
            'presentations': {'ppt', 'pptx'},
            'archives': {'zip', 'rar', '7z'},
            'audio': {'mp3', 'wav', 'ogg', 'm4a'},
            'video': {'mp4', 'avi', 'mov', 'wmv', 'flv'}
        }
        
        # Max file size (10MB)
        self.max_file_size = 10 * 1024 * 1024
    
    def is_allowed_file(self, filename):
        """Check if file extension is allowed"""
        if not filename or '.' not in filename:
            return False, "No file extension found"
        
        extension = filename.rsplit('.', 1)[1].lower()
        
        for file_type, extensions in self.allowed_extensions.items():
            if extension in extensions:
                return True, file_type
        
        return False, "File type not allowed"
    
    def get_file_type(self, filename):
        """Get file type category"""
        if not filename or '.' not in filename:
            return "unknown"
        
        extension = filename.rsplit('.', 1)[1].lower()
        
        for file_type, extensions in self.allowed_extensions.items():
            if extension in extensions:
                return file_type
        
        return "unknown"
    
    def upload_file(self, file, folder="complaints"):
        """Upload file to Cloudinary or development mode storage"""
        try:
            # Check if file is allowed
            is_allowed, file_type_or_error = self.is_allowed_file(file.filename)
            if not is_allowed:
                return {
                    'success': False,
                    'error': file_type_or_error
                }
            
            # Check file size
            file.seek(0, 2)  # Seek to end of file
            file_size = file.tell()
            file.seek(0)  # Reset file pointer
            
            if file_size > self.max_file_size:
                return {
                    'success': False,
                    'error': f"File size exceeds maximum limit of {self.max_file_size // (1024*1024)}MB"
                }
            
            # Generate unique filename
            original_filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            unique_id = str(uuid.uuid4())[:8]
            filename_without_ext = os.path.splitext(original_filename)[0]
            extension = os.path.splitext(original_filename)[1]
            
            unique_filename = f"{filename_without_ext}_{timestamp}_{unique_id}{extension}"
            public_id = f"{folder}/{unique_filename}"
            
            # If Cloudinary is not configured, use development mode
            if not self.is_configured:
                print(f"📦 [DEV MODE] Storing file: {unique_filename}")
                return {
                    'success': True,
                    'data': {
                        'filename': unique_filename,
                        'original_filename': original_filename,
                        'file_url': f"https://via.placeholder.com/300?text={filename_without_ext}", 
                        'file_type': file_type_or_error,
                        'file_size': file_size,
                        'cloudinary_public_id': public_id,
                        'is_development': True
                    }
                }
            
            # Upload to Cloudinary
            if file_type_or_error == 'images':
                # For images, use image upload
                upload_result = cloudinary.uploader.upload(
                    file,
                    public_id=public_id,
                    folder=folder,
                    resource_type="image",
                    quality="auto",
                    fetch_format="auto"
                )
            else:
                # For other files, use raw upload
                upload_result = cloudinary.uploader.upload(
                    file,
                    public_id=public_id,
                    folder=folder,
                    resource_type="raw"
                )
            
            return {
                'success': True,
                'data': {
                    'filename': unique_filename,
                    'original_filename': original_filename,
                    'file_url': upload_result['secure_url'],
                    'file_type': file_type_or_error,
                    'file_size': file_size,
                    'cloudinary_public_id': upload_result['public_id']
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"Upload failed: {str(e)}"
            }
    
    def upload_multiple_files(self, files, folder="complaints"):
        """Upload multiple files to Cloudinary"""
        results = []
        
        for file in files:
            if file and file.filename:
                result = self.upload_file(file, folder)
                results.append({
                    'filename': file.filename,
                    'result': result
                })
        
        return results
    
    def delete_file(self, public_id, resource_type="auto"):
        """Delete file from Cloudinary"""
        try:
            result = cloudinary.uploader.destroy(public_id, resource_type=resource_type)
            return {
                'success': result.get('result') == 'ok',
                'result': result
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_file_info(self, public_id, resource_type="auto"):
        """Get file information from Cloudinary"""
        try:
            result = cloudinary.api.resource(public_id, resource_type=resource_type)
            return {
                'success': True,
                'data': result
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def generate_signed_url(self, public_id, resource_type="auto", expires_in=3600):
        """Generate signed URL for secure file access"""
        try:
            url = cloudinary.utils.cloudinary_url(
                public_id,
                resource_type=resource_type,
                sign_url=True,
                expires_at=expires_in
            )[0]
            
            return {
                'success': True,
                'url': url
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

# Global cloudinary service instance
cloudinary_service = CloudinaryService()

# Wrapper functions for backward compatibility
def upload_to_cloudinary(file, resource_type='raw', folder='uploads', **kwargs):
    """Upload file to Cloudinary with specified resource type (with development mode fallback)"""
    try:
        # Generate unique filename
        from werkzeug.utils import secure_filename
        original_filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        filename_without_ext = os.path.splitext(original_filename)[0]
        extension = os.path.splitext(original_filename)[1]
        
        unique_filename = f"{filename_without_ext}_{timestamp}_{unique_id}{extension}"
        public_id = f"{folder}/{unique_filename}"
        
        # If Cloudinary is not configured, use development mode
        if not cloudinary_service.is_configured:
            print(f"📦 [DEV MODE] Video/File upload: {unique_filename}")
            return {
                'secure_url': f"https://via.placeholder.com/400?text={filename_without_ext}",
                'public_id': public_id,
                'duration': None,
                'width': None,
                'height': None,
                'size': 0,
                'format': extension.strip('.'),
                'resource_type': resource_type,
                'is_development': True
            }
        
        # Determine quality settings based on resource type
        upload_params = {
            'public_id': public_id,
            'folder': folder,
            'resource_type': resource_type
        }
        
        if resource_type == 'video':
            # Video specific parameters
            upload_params.update({
                'quality': 'auto',
                'streaming_profile': 'hls'  # Enable HLS streaming
            })
        elif resource_type == 'image':
            # Image specific parameters
            upload_params.update({
                'quality': 'auto',
                'fetch_format': 'auto'
            })
        
        # Add any additional kwargs
        upload_params.update(kwargs)
        
        file.seek(0)  # Reset file pointer
        upload_result = cloudinary.uploader.upload(file, **upload_params)
        
        return {
            'secure_url': upload_result.get('secure_url'),
            'public_id': upload_result.get('public_id'),
            'duration': upload_result.get('duration'),
            'width': upload_result.get('width'),
            'height': upload_result.get('height'),
            'size': upload_result.get('bytes'),
            'format': upload_result.get('format'),
            'resource_type': upload_result.get('resource_type')
        }
    except Exception as e:
        print(f"❌ Cloudinary upload error: {str(e)}")
        return None

def delete_from_cloudinary(public_id, resource_type='raw'):
    """Delete file from Cloudinary"""
    try:
        result = cloudinary.uploader.destroy(public_id, resource_type=resource_type)
        return result.get('result') == 'ok'
    except Exception as e:
        return False