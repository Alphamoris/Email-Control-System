from typing import List, Optional
import msal
import requests
from datetime import datetime
from app.models.email_account import EmailAccount
from app.models.email import Email
from app.core.config import settings

class OutlookService:
    def __init__(self):
        self.graph_url = "https://graph.microsoft.com/v1.0"
        self.authority = "https://login.microsoftonline.com/common"
        self.scopes = [
            'Mail.Read',
            'Mail.ReadWrite',
            'Mail.Send',
            'User.Read'
        ]

    async def _get_token(self, account: EmailAccount) -> str:
        """Get valid access token for Microsoft Graph API"""
        app = msal.ConfidentialClientApplication(
            settings.MICROSOFT_CLIENT_ID,
            authority=self.authority,
            client_credential=settings.MICROSOFT_CLIENT_SECRET
        )

        if account.access_token and datetime.now() < account.token_expiry:
            return account.access_token

        result = app.acquire_token_by_refresh_token(
            account.refresh_token,
            scopes=self.scopes
        )

        if "access_token" not in result:
            raise Exception("Failed to refresh Microsoft token")

        # Update account tokens
        account.access_token = result["access_token"]
        account.token_expiry = datetime.fromtimestamp(result["expires_in"])
        return account.access_token

    async def fetch_emails(self, account: EmailAccount, limit: int = 100) -> List[Email]:
        """Fetch emails from Outlook"""
        token = await self._get_token(account)
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }

        try:
            response = requests.get(
                f"{self.graph_url}/me/messages?$top={limit}&$select=id,subject,from,toRecipients,ccRecipients,bccRecipients,body,receivedDateTime,isRead",
                headers=headers
            )
            response.raise_for_status()
            messages = response.json().get('value', [])
            
            return [self._parse_outlook_message(msg, account.id) for msg in messages]
        except Exception as e:
            raise Exception(f"Failed to fetch Outlook messages: {str(e)}")

    async def send_email(
        self,
        account: EmailAccount,
        to_addresses: List[str],
        subject: str,
        content: str,
        html_content: Optional[str] = None,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None
    ) -> bool:
        """Send email using Microsoft Graph API"""
        token = await self._get_token(account)
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }

        email_body = {
            "message": {
                "subject": subject,
                "body": {
                    "contentType": "html" if html_content else "text",
                    "content": html_content or content
                },
                "toRecipients": [{"emailAddress": {"address": addr}} for addr in to_addresses]
            }
        }

        if cc:
            email_body["message"]["ccRecipients"] = [
                {"emailAddress": {"address": addr}} for addr in cc
            ]
        if bcc:
            email_body["message"]["bccRecipients"] = [
                {"emailAddress": {"address": addr}} for addr in bcc
            ]

        try:
            response = requests.post(
                f"{self.graph_url}/me/sendMail",
                headers=headers,
                json=email_body
            )
            response.raise_for_status()
            return True
        except Exception as e:
            raise Exception(f"Failed to send Outlook message: {str(e)}")

    async def move_to_folder(self, email: Email, folder: str) -> bool:
        """Move email to a different Outlook folder"""
        token = await self._get_token(email.account)
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }

        folder_id = await self._get_outlook_folder_id(token, folder)
        if not folder_id:
            raise Exception(f"Folder {folder} not found")

        try:
            response = requests.post(
                f"{self.graph_url}/me/messages/{email.message_id}/move",
                headers=headers,
                json={"destinationId": folder_id}
            )
            response.raise_for_status()
            return True
        except Exception as e:
            raise Exception(f"Failed to move Outlook message: {str(e)}")

    async def _get_outlook_folder_id(self, token: str, folder_name: str) -> Optional[str]:
        """Get Outlook folder ID by name"""
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }

        try:
            response = requests.get(
                f"{self.graph_url}/me/mailFolders",
                headers=headers
            )
            response.raise_for_status()
            folders = response.json().get('value', [])
            
            for folder in folders:
                if folder['displayName'].lower() == folder_name.lower():
                    return folder['id']
            return None
        except Exception as e:
            raise Exception(f"Failed to get Outlook folders: {str(e)}")

    def _parse_outlook_message(self, msg: dict, account_id: int) -> Email:
        """Parse Outlook message into Email model"""
        return Email(
            account_id=account_id,
            message_id=msg['id'],
            subject=msg.get('subject', ''),
            sender=msg['from']['emailAddress']['address'],
            recipients=[r['emailAddress']['address'] for r in msg.get('toRecipients', [])],
            cc=[r['emailAddress']['address'] for r in msg.get('ccRecipients', [])] if msg.get('ccRecipients') else None,
            bcc=[r['emailAddress']['address'] for r in msg.get('bccRecipients', [])] if msg.get('bccRecipients') else None,
            content=msg['body']['content'] if msg['body']['contentType'] == 'text' else None,
            html_content=msg['body']['content'] if msg['body']['contentType'] == 'html' else None,
            received_date=datetime.fromisoformat(msg['receivedDateTime'].replace('Z', '+00:00')),
            is_read=msg['isRead'],
            folder='inbox'  # Default to inbox, update based on actual folder
        )
