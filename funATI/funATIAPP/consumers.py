import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User
from django.contrib.auth.models import AnonymousUser
from .models import Message

logger = logging.getLogger(__name__)

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        try:
            # Check if user is authenticated
            if isinstance(self.scope.get("user"), AnonymousUser) or not hasattr(self.scope.get("user"), 'is_authenticated') or not self.scope["user"].is_authenticated:
                logger.warning("Unauthenticated user trying to connect to chat")
                await self.close()
                return

            self.user_id = self.scope["user"].id
            self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
            self.room_group_name = f"chat_{self.room_name}"

            logger.info(f"User {self.scope['user'].username} connecting to room {self.room_name}")

            # Join room group
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )

            await self.accept()
            logger.info(f"User {self.scope['user'].username} connected to room {self.room_name}")
            
        except Exception as e:
            logger.error(f"Error connecting user to chat: {e}")
            try:
                await self.close()
            except:
                pass

    async def disconnect(self, close_code):
        try:
            # Leave room group
            if hasattr(self, 'room_group_name'):
                await self.channel_layer.group_discard(
                    self.room_group_name,
                    self.channel_name
                )
                logger.info(f"User disconnected from room {self.room_name}")
        except Exception as e:
            logger.error(f"Error disconnecting user from chat: {e}")

    async def receive(self, text_data):
        try:
            # Parse message data
            text_data_json = json.loads(text_data)
            message = text_data_json.get("message", "")
            receiver_id = text_data_json.get("receiver_id")

            # Validate required fields
            if not receiver_id:
                logger.error("Missing receiver_id in message")
                await self.send_error("Missing receiver_id")
                return

            if not message.strip():
                logger.error("Empty message content")
                await self.send_error("Message cannot be empty")
                return

            # Validate receiver exists
            receiver_exists = await self.user_exists(receiver_id)
            if not receiver_exists:
                logger.error(f"Receiver {receiver_id} does not exist")
                await self.send_error("Receiver not found")
                return

            logger.info(f"Saving message from {self.user_id} to {receiver_id}")

            # Save message to database
            saved_message = await self.save_message(
                sender_id=self.user_id,
                receiver_id=receiver_id,
                content=message
            )

            if not saved_message:
                await self.send_error("Failed to save message")
                return

            # Send message to room group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "chat_message",
                    "message": message,
                    "sender_id": self.user_id,
                    "sender_username": self.scope["user"].username,
                    "timestamp": saved_message["timestamp"],
                    "message_id": saved_message["id"],
                }
            )

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in message: {e}")
            await self.send_error("Invalid message format")
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            await self.send_error("Error processing message")

    async def chat_message(self, event):
        try:
            message = event["message"]
            sender_id = event["sender_id"]
            sender_username = event["sender_username"]
            timestamp = event["timestamp"]
            message_id = event["message_id"]

            # Send message to WebSocket
            await self.send(text_data=json.dumps({
                "message": message,
                "sender_id": sender_id,
                "sender_username": sender_username,
                "timestamp": timestamp,
                "message_id": message_id,
            }))
        except Exception as e:
            logger.error(f"Error sending chat message: {e}")

    async def send_error(self, error_message):
        """Send error message to the client"""
        try:
            await self.send(text_data=json.dumps({
                "error": error_message,
                "type": "error"
            }))
        except Exception as e:
            logger.error(f"Error sending error message: {e}")

    @database_sync_to_async
    def save_message(self, sender_id, receiver_id, content):
        try:
            sender = User.objects.get(id=sender_id)
            receiver = User.objects.get(id=receiver_id)
            message = Message.objects.create(
                sender=sender,
                receiver=receiver,
                content=content
            )
            return {
                "id": message.id,
                "timestamp": message.timestamp.strftime("%Y-%m-%d %H:%M:%S")
            }
        except User.DoesNotExist as e:
            logger.error(f"User not found: {e}")
            return None
        except Exception as e:
            logger.error(f"Error saving message: {e}")
            return None

    @database_sync_to_async
    def user_exists(self, user_id):
        try:
            return User.objects.filter(id=user_id).exists()
        except Exception as e:
            logger.error(f"Error checking if user exists: {e}")
            return False 