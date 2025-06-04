from google import genai
from google.genai import types
import pyaudio
import os
import wave
import logging
import io
import threading
import concurrent.futures
import time
import re

class SpeechAgent:
    def __init__(self, api_key):
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        self.client=genai.Client(api_key=api_key)
        self.chat=self.client.chats.create(
            model="gemini-2.0-flash",
            config=types.GenerateContentConfig(
                system_instruction="Be concise and brief in your responses. Keep responses under 50 words when possible.",
                max_output_tokens=150
            )
        )
        
        self.FORMAT=pyaudio.paInt16
        self.CHANNELS=1
        self.RECEIVE_SAMPLE_RATE=24000
        self.pya=pyaudio.PyAudio()
        self.RATE=16000
        self.CHUNK=1024

        self.tts_executor = concurrent.futures.ThreadPoolExecutor(max_workers=2)
        self.current_tts_future = None

        self.available_voices = ['Kore', 'Charon', 'Fenrir', 'Aoede']
        self.current_voice = 'Kore' 

        self.emotion_voices = {
            'excited': 'Fenrir',
            'angry': 'Charon', 
            'calm': 'Aoede',
            'happy': 'Kore',
            'serious': 'Charon',
            'energetic': 'Fenrir',
            'peaceful': 'Aoede',
            'neutral': 'Kore'
        }

    def detect_emotion_and_set_voice(self, text):
        """Detect emotion words in text and set appropriate voice"""
        text_lower = text.lower()

        for emotion, voice in self.emotion_voices.items():
            emotion_keywords = {
                'excited': ['excited', 'thrilled', 'amazing', 'fantastic', 'wow'],
                'angry': ['angry', 'mad', 'furious', 'annoyed', 'upset'],
                'calm': ['calm', 'peaceful', 'relax', 'gentle', 'soothing'],
                'happy': ['happy', 'joyful', 'cheerful', 'glad', 'delighted'],
                'serious': ['serious', 'important', 'urgent', 'critical', 'formal'],
                'energetic': ['energetic', 'dynamic', 'powerful', 'strong', 'intense'],
                'peaceful': ['peaceful', 'serene', 'tranquil', 'quiet', 'meditation'],
                'neutral': ['normal', 'regular', 'standard', 'default']
            }
            
            if emotion in emotion_keywords:
                for keyword in emotion_keywords[emotion]:
                    if keyword in text_lower:
                        old_voice = self.current_voice
                        self.current_voice = voice
                        self.logger.info(f"Emotion '{emotion}' detected! Voice changed from {old_voice} to {voice}")
                        return emotion
        return None

    def set_voice(self, voice_name):
        """Set the voice for TTS generation"""
        if voice_name in self.available_voices:
            self.current_voice = voice_name
            self.logger.info(f"Voice set to: {voice_name}")
        else:
            self.logger.warning(f"Unknown voice: {voice_name}. Available: {self.available_voices}")

    def record_audio(self, duration=5):
        print("Recording your audio...")
        stream = self.pya.open(
            format=self.FORMAT,
            channels=self.CHANNELS,
            rate=self.RECEIVE_SAMPLE_RATE,
            input=True,
            frames_per_buffer=self.CHUNK
        )
        frames = []
        for _ in range(0, int(self.RECEIVE_SAMPLE_RATE / self.CHUNK * duration)):
            data = stream.read(self.CHUNK)
            frames.append(data)
        stream.stop_stream()
        stream.close()
        print("Recording complete.")
        audio_data = b''.join(frames)
        return audio_data

    def speech_to_text(self, audio_bytes):
        start_time = time.time()
        wav_buffer=io.BytesIO()
        with wave.open(wav_buffer,'wb') as wav_file:
            wav_file.setnchannels(self.CHANNELS)
            wav_file.setsampwidth(self.pya.get_sample_size(self.FORMAT))
            wav_file.setframerate(self.RATE)
            wav_file.writeframes(audio_bytes)
        wav_data=wav_buffer.getvalue()
        
        response = self.client.models.generate_content(
            model='gemini-2.0-flash',
            contents=[
                'Transcribe this audio',
                types.Part.from_bytes(data=wav_data, mime_type='audio/wav')
            ]
        )
        end_time = time.time()
        self.logger.info(f"Speech-to-text took {end_time - start_time:.2f} seconds")
        return response.text

    def text_to_speech(self, text):
        start_time = time.time()
        try:
            response = self.client.models.generate_content(
                model="gemini-2.5-flash-preview-tts",
                contents=text,
                config=types.GenerateContentConfig(
                    response_modalities=["AUDIO"],
                    speech_config=types.SpeechConfig(
                        voice_config=types.VoiceConfig(
                            prebuilt_voice_config=types.PrebuiltVoiceConfig(
                                voice_name=self.current_voice  # Use selected voice
                            )
                        )
                    )
                )
            )
            end_time = time.time()
            self.logger.info(f"TTS for '{text[:20]}...' with voice {self.current_voice} took {end_time - start_time:.2f} seconds")
            
            if response.candidates and response.candidates[0].content and response.candidates[0].content.parts:
                return response.candidates[0].content.parts[0].inline_data.data
            else:
                return b''
        except Exception as e:
            end_time = time.time()
            self.logger.error(f"TTS error for '{text[:20]}...' after {end_time - start_time:.2f} seconds: {e}")
            return b''

    def play_audio_data(self, audio_data):
        """Play audio data synchronously"""
        if not audio_data:
            return
            
        stream = self.pya.open(
            format=self.FORMAT,
            channels=self.CHANNELS,
            rate=self.RECEIVE_SAMPLE_RATE,
            output=True,
            frames_per_buffer=self.CHUNK
        )
        
        try:

            audio_stream = io.BytesIO(audio_data)
            data = audio_stream.read(self.CHUNK)
            while data:
                stream.write(data)
                data = audio_stream.read(self.CHUNK)
        finally:
            stream.stop_stream()
            stream.close()

    def stream_response(self, message):
        start_time = time.time()

        response = self.chat.send_message(message)
        response_time = time.time()
        self.logger.info(f"Model response generation took {response_time - start_time:.2f} seconds")
        
        current_text = response.text
        print(f"Model response: {current_text}")

        buffer = ""
        buffer += current_text
        
        tts_start_time = time.time()

        while True:
      
            match = re.search(r'^(.*?[.!?])\s', buffer)
            if not match:
                break
                
            sentence = match.group(1).strip()
            buffer = buffer[len(match.group(0)):]  
            
            if sentence:
                self.logger.info(f"Processing sentence: '{sentence[:30]}...'")

                if self.current_tts_future:
                    previous_audio = self.current_tts_future.result()
                    if previous_audio:
                        self.play_audio_data(previous_audio)
 
                self.current_tts_future = self.tts_executor.submit(self.text_to_speech, sentence)

        if buffer.strip():
            self.logger.info(f"Processing remaining text: '{buffer.strip()[:30]}...'")

            if self.current_tts_future:
                previous_audio = self.current_tts_future.result()
                if previous_audio:
                    self.play_audio_data(previous_audio)
       
            remaining_audio = self.text_to_speech(buffer.strip())
            if remaining_audio:
                self.play_audio_data(remaining_audio)
        else:
 
            if self.current_tts_future:
                final_audio = self.current_tts_future.result()
                if final_audio:
                    self.play_audio_data(final_audio)
        
        self.current_tts_future = None
        
        tts_end_time = time.time()
        total_time = tts_end_time - start_time
        self.logger.info(f"Total TTS processing took {tts_end_time - tts_start_time:.2f} seconds")
        self.logger.info(f"Total response generation and processing took {total_time:.2f} seconds")

    def voice_conversation(self, record_duration=5):
        total_start_time = time.time()
        
        input_audio=self.record_audio(record_duration)
        generated_transcript=self.speech_to_text(input_audio)
        print(f"You said {generated_transcript}")
        
        detected_emotion = self.detect_emotion_and_set_voice(generated_transcript)
        if detected_emotion:
            print(f"Detected emotion: {detected_emotion} - Using voice: {self.current_voice}")
        
        self.stream_response(generated_transcript)
        
        total_end_time = time.time()
        self.logger.info(f"Total conversation cycle took {total_end_time - total_start_time:.2f} seconds")

    def cleanup(self):
        if self.current_tts_future:
            self.current_tts_future.cancel()
        self.tts_executor.shutdown(wait=True)
        self.pya.terminate()


def main():
    """Main entry point"""
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        print("Error: GOOGLE_API_KEY environment variable not set")
        print("Please set it in your .env file or export it:")
        print("export GOOGLE_API_KEY='your-api-key-here'")
        return
    
    agent = SpeechAgent(api_key)
    
    try:
        agent.voice_conversation()
    except KeyboardInterrupt:
        print("\nStopping speech agent...")
    finally:
        agent.cleanup()


if __name__ == "__main__":
    main()