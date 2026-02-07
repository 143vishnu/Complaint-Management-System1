import React, { useState, useRef } from 'react';
import { 
  MicrophoneIcon, 
  StopIcon,
  TrashIcon,
  CheckCircleIcon,
  ExclamationCircleIcon,
  SpeakerWaveIcon
} from '@heroicons/react/24/outline';

function VoiceComplaints({ onVoiceSubmit, complaintCategories = [] }) {
  const [isRecording, setIsRecording] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [recordingTime, setRecordingTime] = useState(0);
  const [audioBlob, setAudioBlob] = useState(null);
  
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const timerRef = useRef(null);
  const recognitionRef = useRef(null);

  // Initialize Web Speech API
  const initVoiceRecognition = () => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    
    if (SpeechRecognition) {
      recognitionRef.current = new SpeechRecognition();
      recognitionRef.current.continuous = true;
      recognitionRef.current.interimResults = true;
      recognitionRef.current.lang = 'en-US';
      
      recognitionRef.current.onstart = () => {
        setTranscript('');
        setError('');
      };

      recognitionRef.current.onresult = (event) => {
        let interim = '';
        for (let i = event.resultIndex; i < event.results.length; i++) {
          const transcriptSegment = event.results[i][0].transcript;
          if (event.results[i].isFinal) {
            setTranscript(prev => prev + transcriptSegment + ' ');
          } else {
            interim += transcriptSegment;
          }
        }
      };

      recognitionRef.current.onerror = (event) => {
        setError(`Voice recognition error: ${event.error}`);
        setIsRecording(false);
      };

      recognitionRef.current.onend = () => {
        setIsRecording(false);
        if (timerRef.current) clearInterval(timerRef.current);
      };
    } else {
      setError('Speech Recognition API not supported in your browser');
    }
  };

  // Initialize audio recording
  React.useEffect(() => {
    if (!navigator.mediaDevices) {
      setError('Audio recording not supported in your browser');
      return;
    }

    initVoiceRecognition();

    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.stop();
      }
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
    };
  }, []);

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];
      
      mediaRecorder.ondataavailable = (event) => {
        audioChunksRef.current.push(event.data);
      };
      
      mediaRecorder.onstop = () => {
        const blob = new Blob(audioChunksRef.current, { type: 'audio/wav' });
        setAudioBlob(blob);
      };
      
      mediaRecorder.start();
      setIsRecording(true);
      setRecordingTime(0);
      setError('');
      setSuccess('');
      
      // Start voice recognition
      if (recognitionRef.current) {
        recognitionRef.current.start();
      }
      
      // Timer for recording duration
      timerRef.current = setInterval(() => {
        setRecordingTime(prev => prev + 1);
      }, 1000);
      
    } catch (err) {
      setError(`Failed to start recording: ${err.message}`);
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      mediaRecorderRef.current.stream.getTracks().forEach(track => track.stop());
      
      if (recognitionRef.current) {
        recognitionRef.current.stop();
      }
      
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
      
      setIsRecording(false);
    }
  };

  const playback = () => {
    if (audioBlob) {
      const audioUrl = URL.createObjectURL(audioBlob);
      const audio = new Audio(audioUrl);
      audio.play();
    }
  };

  const reset = () => {
    setTranscript('');
    setAudioBlob(null);
    setRecordingTime(0);
    setError('');
  };

  const handleSubmit = async () => {
    if (!transcript.trim()) {
      setError('Please provide a complaint description');
      return;
    }

    if (onVoiceSubmit) {
      console.log('🎤 Submitting voice complaint...', {
        description: transcript.trim(),
        hasAudio: !!audioBlob,
        duration: recordingTime
      });

      const success = await onVoiceSubmit({
        description: transcript.trim(),
        audioBlob: audioBlob,
        duration: recordingTime
      });

      console.log('✅ Voice submission result:', success);

      if (success) {
        setSuccess('Voice complaint submitted successfully!');
        reset();
      } else {
        console.error('❌ Voice complaint submission failed');
      }
    } else {
      console.error('❌ onVoiceSubmit callback not defined');
      setError('Voice submission handler not available');
    }
  };

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const browserSupported = !!navigator.mediaDevices && (window.SpeechRecognition || window.webkitSpeechRecognition);

  if (!browserSupported) {
    return (
      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
        <div className="flex items-center">
          <ExclamationCircleIcon className="h-5 w-5 text-yellow-600 mr-3" />
          <span className="text-sm text-yellow-700">
            Voice complaints are not supported in your browser. Please use Chrome, Edge, or Safari.
          </span>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h3 className="font-semibold text-blue-900 mb-2 flex items-center">
          <MicrophoneIcon className="h-5 w-5 mr-2" />
          Voice Complaint Recording
        </h3>
        <p className="text-sm text-blue-700">
          Click the microphone to start recording. Speak your complaint naturally, and it will be transcribed automatically.
        </p>
      </div>

      {/* Recording Controls */}
      <div className="flex flex-col items-center space-y-4">
        <button
          onClick={isRecording ? stopRecording : startRecording}
          className={`p-6 rounded-full transition-all duration-200 ${
            isRecording
              ? 'bg-red-500 hover:bg-red-600 animate-pulse'
              : 'bg-blue-500 hover:bg-blue-600'
          } text-white shadow-lg`}
        >
          {isRecording ? (
            <StopIcon className="h-8 w-8" />
          ) : (
            <MicrophoneIcon className="h-8 w-8" />
          )}
        </button>

        {isRecording && (
          <div className="text-center">
            <p className="text-sm font-mono text-gray-600">
              Recording: {formatTime(recordingTime)}
            </p>
            <p className="text-xs text-gray-500 mt-1">Listening...</p>
          </div>
        )}
      </div>

      {/* Transcript Display */}
      {transcript && (
        <div className="bg-gray-50 border border-gray-300 rounded-lg p-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Transcribed Text
          </label>
          <textarea
            value={transcript}
            onChange={(e) => setTranscript(e.target.value)}
            rows={4}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
            placeholder="Edit your complaint text here..."
          />
        </div>
      )}

      {/* Audio Playback */}
      {audioBlob && (
        <div className="bg-gray-50 border border-gray-300 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-700">Audio Recording</p>
              <p className="text-xs text-gray-500">Duration: {formatTime(recordingTime)}</p>
            </div>
            <button
              onClick={playback}
              className="inline-flex items-center px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition"
            >
              <SpeakerWaveIcon className="h-4 w-4 mr-2" />
              Play
            </button>
          </div>
        </div>
      )}

      {/* Error Messages */}
      {error && (
        <div className="flex items-center p-3 bg-red-50 border border-red-200 rounded-lg">
          <ExclamationCircleIcon className="h-5 w-5 text-red-500 mr-2" />
          <span className="text-sm text-red-700">{error}</span>
        </div>
      )}

      {/* Success Messages */}
      {success && (
        <div className="flex items-center p-3 bg-green-50 border border-green-200 rounded-lg">
          <CheckCircleIcon className="h-5 w-5 text-green-500 mr-2" />
          <span className="text-sm text-green-700">{success}</span>
        </div>
      )}

      {/* Action Buttons */}
      {transcript && (
        <div className="flex gap-3">
          <button
            onClick={reset}
            className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition flex items-center justify-center"
          >
            <TrashIcon className="h-4 w-4 mr-2" />
            Clear
          </button>
          <button
            onClick={handleSubmit}
            className="flex-1 px-4 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 transition flex items-center justify-center"
          >
            <CheckCircleIcon className="h-4 w-4 mr-2" />
            Submit Complaint
          </button>
        </div>
      )}
    </div>
  );
}

export default VoiceComplaints;
