import threading
import queue
import time
from abc import ABC, abstractmethod
from typing import Callable
from dataclasses import dataclass
import ChatAIStream as cas

streamParams = cas.streamParams
userMessage = cas.userMessage
aiParams = cas.aiParams

class voiceGenerator(ABC):
  @abstractmethod
  def generate(self, text):
    pass

@dataclass
class params(cas.params):
  voice_generator : voiceGenerator = None
  answer_with_voice_cb: Callable[[userMessage, any, any], None] = None

@dataclass
class answerSlot():
  user_message: any
  completion: any

class ChatAIStreamer(cas.ChatAIStream):
  def __generateVoice(self):
    while self.__keeping_connection:
      if self.__answer_queue.empty():
        time.sleep(0.01)
      else:
        answer_slot = self.__answer_queue.get()
        text, voice = self.voice_generator.generate(text=answer_slot.completion.choices[0]["message"]["content"])
        answer_slot.completion.choices[0]["message"]["content"] = text
        if self.answer_with_voice_cb:
          self.answer_with_voice_cb(answer_slot.user_message, answer_slot.completion, voice)

  def my_answer_cb(self, user_message, completion):
    if self.answer_cb:
      self.answer_cb(user_message, completion)
    if self.voice_generator:
      while self.__keeping_connection and self.__answer_queue.full():
        time.sleep(0.01)
      if self.__keeping_connection:
        self.__answer_queue.put(answerSlot(user_message=user_message, completion=completion))

  def __init__(self, params):
    self.__keeping_connection = False
    self.voice_generator = params.voice_generator
    self.__answer_queue = None
    self.__answer_thread = None
    if (self.voice_generator):
      self.__answer_queue = queue.Queue(5)
      self.__answer_thread = threading.Thread(target=self.__generateVoice, daemon=True)
    self.answer_with_voice_cb = params.answer_with_voice_cb

    self.answer_cb = params.ai_params.answer_cb
    params.ai_params.answer_cb = self.my_answer_cb
    super(ChatAIStreamer, self).__init__(params)

  def run(self):
    self.__keeping_connection = True
    self.__answer_thread.start()
    super(ChatAIStreamer, self).run()

  def disconnect(self):
    super(ChatAIStreamer, self).disconnect()
    self.__keeping_connection = False
