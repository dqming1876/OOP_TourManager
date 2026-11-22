"""Shared destination editor, with authorization and optimistic concurrency."""
from urllib.parse import urlsplit
from uuid import uuid4
from .domain import ADMIN, ConflictError, ValidationError, integer_between, required_text
from .ports import DestinationsPort


class DestinationsService:
    def __init__(self, repository: DestinationsPort, access):
        self.repository = repository
        self.access = access

    async def entries(self):
        return await self.repository.list_entries()

    async def save(self, entry_id, body):
        self.access.require_role(ADMIN)
        province_id = integer_between(body.get('province_id'), 1, 34, 'Tỉnh thành', 'province_id')
        kind = body.get('kind')
        if kind not in ('attractions', 'specialties'):
            raise ValidationError('Loại danh mục không hợp lệ.', 'kind')
        values = {'province_id': province_id, 'kind': kind}
        for name, limit in [('name', 120), ('description', 4000), ('url', 2000), ('source', 250)]:
            values[name] = required_text(body.get(name), limit, name, name)
        url = urlsplit(values['url'])
        if url.scheme != 'https' or not url.hostname or url.username or url.password:
            raise ValidationError('Dùng địa chỉ ảnh HTTPS hợp lệ.', 'url')
        version = self.version(body) if entry_id else None
        if not await self.repository.save_entry(entry_id or str(uuid4()), values, version):
            raise ConflictError('Tên đã tồn tại hoặc dữ liệu đã thay đổi. Vui lòng tải lại danh mục.')

    @staticmethod
    def version(body):
        return integer_between(body.get('version'), 1, 2**31 - 1, 'Phiên bản', 'version')

    async def remove(self, entry_id, body):
        self.access.require_role(ADMIN)
        if not await self.repository.remove_entry(entry_id, self.version(body)):
            raise ConflictError('Dữ liệu đã thay đổi hoặc đây là mục cuối của danh sách. Vui lòng tải lại.')
