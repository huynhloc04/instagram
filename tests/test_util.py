import unittest
from app.v1.utils import allowed_file


class TestUnits(unittest.TestCase):

    #   Test case #1: Valid extension
    def test_allowd_extension_lower(self):
        self.assertTrue(allowed_file("filename.jpg"), "Test failed for filename.jpg")
        self.assertTrue(allowed_file("photo.png"), "Test failed for photo.png")
        self.assertTrue(allowed_file("picture.gif"), "Test failed for picture.gif")
        self.assertTrue(
            allowed_file("animation.jpeg"), "Test failed for animation.jpeg"
        )
        self.assertTrue(allowed_file("document.pdf"), "Test failed for document.pdf")

    #   Test case #2: Valid extension, but mix lower and upper case
    def test_allowed_extension_upper(self):
        self.assertTrue(allowed_file("filename.JPG"), "Test failed for filename.JPG")
        self.assertTrue(allowed_file("photo.pNG"), "Test failed for photo.pNG")
        self.assertTrue(allowed_file("picture.Gif"), "Test failed for picture.Gif")
        self.assertTrue(
            allowed_file("animation.jPEg"), "Test failed for animation.jPEg"
        )

    #   Test case #3: Invalid extension
    def test_disallowed_extension(self):
        self.assertFalse(allowed_file("archive.zip"), "Test failed for archive.zip")
        self.assertFalse(allowed_file("demo.py"), "Test failed for demo.py")
        self.assertFalse(
            allowed_file("animation.jpgc"), "Test failed for animation.jpgc"
        )

    # Test case #4: Filename have multiple dot characters
    def test_multiple_dots(self):
        self.assertFalse(
            allowed_file("archive.zip.tar"), "Test failed for archive.zip.tar"
        )
        self.assertTrue(allowed_file("demo.py.JPEG"), "Test failed for demo.py.JPEG")
        self.assertFalse(
            allowed_file("animation.txt.jpgc"), "Test failed for animation.txt.jpgc"
        )

    # Test case #5: Only has extension
    def test_only_extension(self):
        self.assertTrue(allowed_file(".jpg"), "Test failed for .jpg")
        self.assertTrue(allowed_file(".tar"), "Test failed for .tar")

    # Test case #6: No extension
    def test_only_extension(self):
        self.assertFalse(allowed_file("document"), "Test failed for document")
        self.assertFalse(allowed_file("archive"), "Test failed for archive")

    # Test case #7: Empty string or only dot
    def test_empty_or_dot(self):
        self.assertFalse(allowed_file(""), "Test failed for empty string")
        self.assertFalse(allowed_file("."), "Test failed for only dot")


if __name__ == "__main__":
    unittest.main()
