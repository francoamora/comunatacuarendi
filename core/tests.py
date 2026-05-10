from django.test import SimpleTestCase

from .models import Video


class VideoEmbedUrlTests(SimpleTestCase):
    def test_youtube_watch_url_uses_privacy_enhanced_embed(self):
        video = Video(url="https://www.youtube.com/watch?v=abc123XYZ_0")

        self.assertEqual(
            video.embed_url,
            "https://www.youtube-nocookie.com/embed/abc123XYZ_0?rel=0&playsinline=1",
        )

    def test_youtube_short_url_uses_embed_path(self):
        video = Video(url="https://www.youtube.com/shorts/shorts123")

        self.assertEqual(
            video.embed_url,
            "https://www.youtube-nocookie.com/embed/shorts123?rel=0&playsinline=1",
        )

    def test_youtu_be_url_uses_embed_path(self):
        video = Video(url="https://youtu.be/compact123?si=tracking")

        self.assertEqual(
            video.embed_url,
            "https://www.youtube-nocookie.com/embed/compact123?rel=0&playsinline=1",
        )
