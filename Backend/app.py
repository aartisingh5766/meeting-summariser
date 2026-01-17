from flask import Flask, request, jsonify, render_template_string
from moviepy.editor import VideoFileClip
import os
from dotenv import load_dotenv
import tempfile
import requests
import base64
from flask_cors import CORS

load_dotenv()

app = Flask(__name__)
CORS(app)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# File type validation
ALLOWED_VIDEO_EXTENSIONS = {'.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv', '.m4v'}
ALLOWED_AUDIO_EXTENSIONS = {'.mp3', '.wav', '.m4a', '.ogg', '.aac', '.flac'}
ALLOWED_EXTENSIONS = ALLOWED_VIDEO_EXTENSIONS | ALLOWED_AUDIO_EXTENSIONS

def allowed_file(filename):
    """Check if file extension is allowed"""
    return os.path.splitext(filename.lower())[1] in ALLOWED_EXTENSIONS

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Meeting Summary Generator</title>
    <style>
        body { 
            font-family: Arial, sans-serif; 
            max-width: 900px; 
            margin: 50px auto; 
            padding: 20px;
            background: #f5f5f5;
        }
        .container {
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1 {
            color: #333;
            text-align: center;
        }
        .info-box {
            background: #e8f4fd;
            border-left: 4px solid #4285f4;
            padding: 15px;
            margin: 20px 0;
            border-radius: 5px;
        }
        .info-box ul {
            margin: 10px 0;
            padding-left: 20px;
        }
        .upload-box { 
            border: 2px dashed #4285f4; 
            padding: 40px; 
            text-align: center;
            border-radius: 8px;
            margin: 20px 0;
            background: #f8f9fa;
        }
        input[type="file"] {
            margin: 10px 0;
        }
        button { 
            background: #4285f4; 
            color: white; 
            padding: 12px 30px; 
            border: none; 
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
            margin-top: 10px;
        }
        button:hover {
            background: #357ae8;
        }
        button:disabled {
            background: #ccc;
            cursor: not-allowed;
        }
        #status { 
            margin-top: 20px; 
            padding: 15px;
            text-align: center;
            font-weight: bold;
        }
        #result { 
            margin-top: 20px; 
            padding: 20px;
            background: #f8f9fa;
            border-radius: 8px;
            line-height: 1.6;
        }
        .loading {
            color: #4285f4;
        }
        .success {
            color: #0f9d58;
        }
        .error {
            color: #db4437;
        }
        .file-info {
            margin: 10px 0;
            color: #666;
            font-size: 14px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎥 Meeting Summary Generator</h1>
        <p style="text-align: center; color: #666;">
            Upload your meeting recording to get an AI-powered summary
        </p>
        
        <div class="info-box">
            <strong>📌 Supported Files:</strong>
            <ul>
                <li><strong>Video:</strong> MP4, AVI, MOV, MKV, WebM, FLV</li>
                <li><strong>Audio:</strong> MP3, WAV, M4A, OGG, AAC</li>
                <li><strong>Max Size:</strong> 50MB</li>
                <li><strong>Best For:</strong> Meetings, Interviews, Lectures, Podcasts</li>
            </ul>
        </div>
        
        <div class="upload-box">
            <input type="file" id="videoFile" accept="video/*,audio/*">
            <div id="fileInfo" class="file-info"></div>
            <br>
            <button id="submitBtn" disabled>📊 Generate Summary</button>
        </div>
        
        <div id="status"></div>
        <div id="result"></div>
    </div>
    
    <script>
        const allowedExtensions = [
            '.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv', '.m4v',
            '.mp3', '.wav', '.m4a', '.ogg', '.aac', '.flac'
        ];
        
        const fileInput = document.getElementById('videoFile');
        const fileInfo = document.getElementById('fileInfo');
        const submitBtn = document.getElementById('submitBtn');
        const status = document.getElementById('status');
        const result = document.getElementById('result');
        
        fileInput.addEventListener('change', validateFile);
        submitBtn.addEventListener('click', uploadVideo);
        
        function validateFile() {
            const file = fileInput.files[0];
            
            if (!file) {
                submitBtn.disabled = true;
                fileInfo.textContent = '';
                return;
            }
            
            const fileName = file.name.toLowerCase();
            const fileExt = fileName.substring(fileName.lastIndexOf('.'));
            const fileSizeMB = (file.size / (1024 * 1024)).toFixed(2);
            
            if (!allowedExtensions.includes(fileExt)) {
                fileInfo.style.color = '#db4437';
                fileInfo.textContent = '❌ Unsupported file type: ' + fileExt;
                submitBtn.disabled = true;
                return;
            }
            
            if (file.size > 50 * 1024 * 1024) {
                fileInfo.style.color = '#db4437';
                fileInfo.textContent = '❌ File too large: ' + fileSizeMB + 'MB (max 50MB)';
                submitBtn.disabled = true;
                return;
            }
            
            fileInfo.style.color = '#0f9d58';
            fileInfo.textContent = '✅ ' + file.name + ' (' + fileSizeMB + 'MB)';
            submitBtn.disabled = false;
        }
        
        async function uploadVideo() {
            const file = fileInput.files[0];
            
            if (!file) { 
                alert('Please select a file'); 
                return; 
            }
            
            submitBtn.disabled = true;
            submitBtn.textContent = '⏳ Processing...';
            
            status.className = 'loading';
            status.textContent = '⏳ Uploading and processing... This may take a few minutes.';
            result.innerHTML = '';
            
            const formData = new FormData();
            formData.append('video', file);
            
            try {
                const response = await fetch('/process', {
                    method: 'POST',
                    body: formData
                });
                const data = await response.json();
                
                if (data.success) {
                    const summaryText = data.summary || '';
                    const lines = summaryText.split('\\n');
                    const formattedSummary = lines.join('<br>');
                    
                    result.innerHTML = '<h2>📝 Meeting Summary:</h2><hr>' + formattedSummary;
                    status.className = 'success';
                    status.textContent = '✅ Summary generated successfully!';
                } else {
                    status.className = 'error';
                    status.textContent = '❌ Error: ' + data.error;
                }
            } catch (error) {
                status.className = 'error';
                status.textContent = '❌ Error: ' + error.message;
            } finally {
                submitBtn.disabled = false;
                submitBtn.textContent = '📊 Generate Summary';
            }
        }
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/favicon.ico')
def favicon():
    return '', 204

@app.route('/process', methods=['POST'])
def process_video():
    try:
        if 'video' not in request.files:
            return jsonify({'success': False, 'error': 'No file uploaded'})
        
        video_file = request.files['video']
        
        if video_file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'})
        
        if not allowed_file(video_file.filename):
            return jsonify({'success': False, 'error': 'Unsupported file type'})
        
        # Check file size before processing
        video_file.seek(0, os.SEEK_END)
        file_size = video_file.tell()
        video_file.seek(0)
        file_size_mb = file_size / (1024 * 1024)
        
        # Limit to 50MB
        if file_size_mb > 50:
            return jsonify({
                'success': False, 
                'error': f'File too large ({file_size_mb:.1f}MB). Please use a file smaller than 50MB.'
            })
        
        file_ext = os.path.splitext(video_file.filename.lower())[1]
        is_audio_only = file_ext in ALLOWED_AUDIO_EXTENSIONS
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as temp_file:
            video_file.save(temp_file.name)
            temp_file_path = temp_file.name
        
        print(f"Processing {'audio' if is_audio_only else 'video'}: {video_file.filename} ({file_size_mb:.2f}MB)")
        
        if is_audio_only:
            audio_path = temp_file_path
        else:
            print("Extracting audio...")
            audio_path = extract_audio(temp_file_path)
            os.remove(temp_file_path)
        
        print("Generating summary...")
        summary = generate_summary_with_gemini(audio_path)
        
        os.remove(audio_path)
        
        return jsonify({'success': True, 'summary': summary})
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

def extract_audio(video_path):
    """Extract audio from video file"""
    try:
        video = VideoFileClip(video_path)
        audio_path = tempfile.mktemp(suffix='.mp3')
        video.audio.write_audiofile(audio_path, verbose=False, logger=None)
        video.close()
        return audio_path
    except Exception as e:
        raise Exception(f"Failed to extract audio: {str(e)}")

def generate_summary_with_gemini(audio_path):
    """Use Gemini API with inline base64 audio - Smart detection"""
    try:
        print("Reading audio file...")
        
        with open(audio_path, 'rb') as f:
            audio_data = base64.b64encode(f.read()).decode('utf-8')
        
        print("Sending to Gemini API...")
        
        url = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
        
        payload = {
            "contents": [{
                "parts": [
                    {
                        "inline_data": {
                            "mime_type": "audio/mpeg",
                            "data": audio_data
                        }
                    },
                    {
                        "text": """Analyze this audio and provide a detailed response:

**1. Content Classification**
Identify the type of audio (meeting, song, podcast, interview, lecture, etc.)

**2. Transcription/Content Description**
- If it's speech/dialogue: Provide key quotes and what was said
- If it's music/song: Describe the lyrics theme, genre, mood (without reproducing full lyrics)
- If it's a mix: Describe what you hear

**3. Structured Summary**
Based on the content type, provide:
- **For Meetings**: Discussion points, decisions, action items, next steps
- **For Songs**: Title (if known), artist (if known), theme, genre, mood, key message
- **For Lectures**: Main topics, key concepts, takeaways
- **For Interviews**: Participants, topics discussed, key insights
- **For Other Content**: Appropriate categorized summary

**4. Key Details**
- Language(s) spoken/sung
- Duration estimate
- Quality of audio
- Any notable elements

Be comprehensive and specific about what you actually detect in the audio."""
                    }
                ]
            }]
        }
        
        response = requests.post(url, json=payload, timeout=120)
        
        if response.status_code != 200:
            raise Exception(f"API error ({response.status_code}): {response.text}")
        
        result = response.json()
        summary = result['candidates'][0]['content']['parts'][0]['text']
        
        print("✅ Summary generated!")
        return summary
        
    except Exception as e:
        raise Exception(f"Gemini API error: {str(e)}")


if __name__ == '__main__':
    print("🚀 Starting Meeting Summary Generator...")
    print("📍 Server running at http://localhost:5000")
    if not GEMINI_API_KEY:
        print("⚠️  WARNING: GEMINI_API_KEY not found in .env file!")
    else:
        print(f"✅ API Key loaded")
    app.run(debug=True, port=5000, host='0.0.0.0')