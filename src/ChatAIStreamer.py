from abc import ABC, abstractmethod
from dataclasses import dataclass
import ChatAIStream as cas

streamParams = cas.streamParams
aiParams = cas.aiParams

class voiceGenerator(ABC):
  @abstractmethod
  def generate(self, text):
    pass

@dataclass
class params(cas.params):
  voice_generator : voiceGenerator = None

class ChatAIStreamer(cas.ChatAIStream):
  def my_answer_cb(self, user_message, completion):
    if self.answer_cb:
      voice = None
      if (self.voice_generator):
        text, voice = self.voice_generator.generate(text=completion.choices[0]["message"]["content"])
        completion.choices[0]["message"]["content"] = text
      self.answer_cb(user_message, completion, voice)

  def __init__(self, params):
    self.voice_generator = params.voice_generator
    self.answer_cb = params.ai_params.answer_cb
    params.ai_params.answer_cb = self.my_answer_cb
    super(ChatAIStreamer, self).__init__(params)
