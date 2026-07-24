import pytest


class TestParseAttaches:
    def test_none_attaches(self, sample_vanus):
        result = sample_vanus.parse_attaches_to_obj(None)
        assert result == {}

    def test_empty_list(self, sample_vanus):
        result = sample_vanus.parse_attaches_to_obj([])
        assert result == {}

    def test_photo_attach(self, sample_vanus):
        attaches = [{"_type": "PHOTO", "photoToken": "abc", "url": "https://ex.com/p.jpg", "height": 300, "width": 400}]
        result = sample_vanus.parse_attaches_to_obj(attaches)
        assert len(result["photo"]) == 1
        assert result["photo"][0]["token"] == "abc"
        assert result["photo"][0]["url"] == "https://ex.com/p.jpg"

    def test_video_attach(self, sample_vanus):
        attaches = [{"_type": "VIDEO", "token": "vid1", "thumbnail": "https://ex.com/t.jpg", "height": 720, "width": 1280, "duration": 30}]
        result = sample_vanus.parse_attaches_to_obj(attaches)
        assert len(result["video"]) == 1
        assert result["video"][0]["token"] == "vid1"
        assert result["video"][0]["duration"] == 30

    def test_audio_attach(self, sample_vanus):
        attaches = [{"_type": "AUDIO", "token": "aud1", "url": "https://ex.com/a.mp3", "duration": 120}]
        result = sample_vanus.parse_attaches_to_obj(attaches)
        assert result["audio"] is not None
        assert result["audio"]["token"] == "aud1"

    def test_file_attach(self, sample_vanus):
        attaches = [{"_type": "FILE", "name": "doc.pdf", "size": 1024, "preview": {"_type": "PHOTO", "url": "https://ex.com/preview.jpg", "height": 100, "width": 100}}]
        result = sample_vanus.parse_attaches_to_obj(attaches)
        assert result["document"] is not None
        assert result["document"]["name"] == "doc.pdf"
        assert result["document"]["type"] == "photo"

    def test_multiple_attaches(self, sample_vanus):
        attaches = [
            {"_type": "PHOTO", "photoToken": "p1", "url": "https://ex.com/1.jpg", "height": 100, "width": 100},
            {"_type": "PHOTO", "photoToken": "p2", "url": "https://ex.com/2.jpg", "height": 200, "width": 200},
            {"_type": "VIDEO", "token": "v1", "thumbnail": "https://ex.com/v.jpg", "height": 720, "width": 1280, "duration": 30},
        ]
        result = sample_vanus.parse_attaches_to_obj(attaches)
        assert len(result["photo"]) == 2
        assert len(result["video"]) == 1

    def test_unknown_type_ignored(self, sample_vanus):
        attaches = [{"_type": "UNKNOWN", "data": "something"}]
        result = sample_vanus.parse_attaches_to_obj(attaches)
        assert result["photo"] == []
        assert result["video"] == []
        assert result["audio"] is None
        assert result["document"] is None

    def test_file_with_video_preview(self, sample_vanus):
        attaches = [{"_type": "FILE", "name": "video.mp4", "size": 5000, "preview": {"_type": "VIDEO", "thumbnail": "https://ex.com/vid_preview.jpg", "height": 480, "width": 640, "duration": 15}}]
        result = sample_vanus.parse_attaches_to_obj(attaches)
        assert result["document"]["type"] == "video"
        assert result["document"]["duration"] == 15
