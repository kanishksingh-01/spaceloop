class ObjectStorage:
    def upload(self, file_bytes, filename):
        return f"/uploads/{filename}"
