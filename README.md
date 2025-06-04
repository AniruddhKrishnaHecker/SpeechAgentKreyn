

---

# Agent: SpeechAgentKreyn – Real-Time Emotional Voice AI

## Description

This project demonstrates a real-time audio-to-audio conversational agent using Google's Gemini API. The agent records your voice, transcribes it, analyzes emotional tone, and responds with expressive voice synthesis. Voice style is automatically chosen based on detected sentiment, providing more natural and emotionally appropriate responses.

## Model Used

* **`gemini-2.0-flash`**
  Used for transcription and conversational text generation.

* **`gemini-2.5-flash-preview-tts`**
  Used for streaming text-to-speech synthesis with support for stylized voices.

## Capabilities Overview

| Feature                       | Supported | Notes                                                 |
| ----------------------------- | --------- | ----------------------------------------------------- |
| **Interaction Mode**          |           |                                                       |
| Audio-to-Audio (Local Mic)    | ✔         | Uses `PyAudio` for microphone input                   |
| **Input Modalities**          |           |                                                       |
| Audio (Mic Input)             | ✔         | Real-time recording using PyAudio                     |
| Text (Internally Generated)   | ✔         | Transcription from user audio                         |
| **Output Modalities**         |           |                                                       |
| Audio (TTS)                   | ✔         | Stylized response voice generation                    |
| Text (Terminal Output)        | ✔         | Transcripts and log info                              |
| **Core AI Capabilities**      |           |                                                       |
| Speech Recognition            | ✔         | Gemini STT                                            |
| Emotion-Driven Voice Switch   | ✔         | Heuristic detection via keywords                      |
| Text-to-Speech (Streaming)    | ✔         | Gemini 2.5 flash TTS                                  |
| Voice Selection               | ✔         | Available voices: Kore, Fenrir, Aoede, Charon         |
| Sentence-wise Audio Streaming | ✔         | TTS responses are played sentence by sentence         |
| Multithreaded TTS Handling    | ✔         | Thread pool used to handle concurrent speech playback |

## Setup & How to Run

### 1. Prerequisites

* Python 3.9+
* [uv package manager](https://github.com/astral-sh/uv)
* Google API Key with access to Gemini endpoints

Install system dependencies (Linux users only):

```bash
sudo apt update && sudo apt install python3-dev portaudio19-dev pkg-config
```

### 2. Clone the Repository

```bash
git clone https://github.com/AniruddhKrishnaHecker/SpeechAgentKreyn.git
cd SpeechAgentKreyn
```

### 3. Set Environment Variable

Export your API key:

```bash
export GOOGLE_API_KEY="your_api_key_here"
```

This is required for all Gemini API requests.

### 4. Set Up Virtual Environment & Install Dependencies

```bash
uv venv
source .venv/bin/activate   # On Windows: .venv\Scripts\activate
uv pip install -r requirements.txt
```

> `uv` ensures deterministic dependency resolution and better performance than pip.

### 5. Run the Agent

```bash
python VtV_v2.py
```

This will:

* Record 5 seconds of speech from the microphone
* Transcribe using Gemini STT
* Detect emotional tone and choose an appropriate voice
* Generate and play back a response using Gemini TTS

## Available Voices & Emotions

| Emotion   | Voice  |
| --------- | ------ |
| excited   | Fenrir |
| angry     | Charon |
| calm      | Aoede  |
| happy     | Kore   |
| serious   | Charon |
| energetic | Fenrir |
| peaceful  | Aoede  |
| neutral   | Kore   |

Voice style is automatically chosen based on keywords found in the transcript. You may also override the voice manually using:

```python
agent.set_voice("Fenrir")
```

## Example Interaction

After running the agent, speak something like:

> “I’m so thrilled to test this!”

Terminal output:

```
Recording your audio...
Recording complete.
You said: I’m so thrilled to test this!
Emotion 'excited' detected! Voice changed from Kore to Fenrir
Model response: That sounds awesome! I'm excited too!
```

The voice response will then be played back using the "Fenrir" voice.

## Example Customization

To use a specific voice and bypass emotion detection:

```python
agent.set_voice("Aoede")
agent.voice_conversation()
```

## Cleanup

Resources are cleaned up automatically after the conversation ends.
You may also call manually:

```python
agent.cleanup()
```

This shuts down the thread pool and terminates PyAudio cleanly.

## Structure

* `VtV_v2.py`: Main implementation of the agent

  * Includes recording, transcription, emotion parsing, TTS generation, and audio playback


---


