# -*- coding: utf-8-*-
import logging
from notifier import Notifier
from brain import Brain
import requests
from modules import House

class Conversation(object):

    def __init__(self, persona, mic, profile):
        self._logger = logging.getLogger(__name__)
        self.persona = persona
        self.mic = mic
        self.profile = profile
        self.brain = Brain(mic, profile)
        self.notifier = Notifier(profile)
        self.radioPaused = False

    def determineIntent(self, input):
        if (len(input) == 0):
            return {}
        
        print input[0]
        parameters = {"q" : input[0].lower()}
        r = requests.post('https://api.wit.ai/message?v=20150524',
                      headers={ 'Authorization': 'Bearer TBYTRFCCBMHAKHHDKDCR7JTPMKNSVLOS',
                     'accept': 'application/json'},
                     params=parameters)
                     
        print r.url
        
        try:
            r.raise_for_status()
            text = r.json()['outcomes']
            self._logger.info(len(r.json()["outcomes"]))
        except requests.exceptions.HTTPError:
            self._logger.critical('Request failed with response: %r',
                                  r.text,
                                  exc_info=True)
            return []
        except requests.exceptions.RequestException:
            self._logger.critical('Request failed.', exc_info=True)
            return []
        except ValueError as e:
            self._logger.critical('Cannot parse response: %s',
                                  e.args[0])
            return []
        except KeyError:
            self._logger.critical('Cannot parse response.',
                                  exc_info=True)
            return []
        else:
            transcribed = text[0]
            self._logger.info('Intent: %r', transcribed)
            return transcribed

    def handleForever(self):
        """
        Delegates user input to the handling function when activated.
        """
        self._logger.info("Starting to handle conversation with keyword '%s'.",
                          self.persona)
        while True:
            # Print notifications until empty
            notifications = self.notifier.getAllNotifications()
            for notif in notifications:
                self._logger.info("Received notification: '%s'", str(notif))

            self._logger.debug("Started listening for keyword '%s'",
                               self.persona)
            threshold, transcribed = self.mic.passiveListen(self.persona)
            self._logger.debug("Stopped listening for keyword '%s'",
                               self.persona)

            if not transcribed or not threshold:
                self._logger.info("Nothing has been said or transcribed.")
                continue
            
            # Pause the radio
            if House.radioPlaying():
                self.radioPaused = True
                self._logger.info("Pausing radio...")
                House.stopRadio()
            
            self._logger.info("Keyword '%s' has been said!", self.persona)

            self._logger.debug("Started to listen actively with threshold: %r",
                               threshold)
            input = self.mic.activeListenToAllOptions(threshold)
            self._logger.debug("Stopped to listen actively with threshold: %r",
                               threshold)
            
            if (len(input) > 1):
                intent = input[1]
                input = [input[0]]
            else:
                intent = self.determineIntent(input)
            
            if input:
                self.brain.query(input,intent)
            else:
                self.mic.say("Pardon?")
            
            # Resume if necessary
            if self.radioPaused == True:
                self.radioPaused = False
                self._logger.info("Resuming radio...")
                House.startRadio()
