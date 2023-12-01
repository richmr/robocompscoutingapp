from pathlib import Path
import pytest

from robocompscoutingapp.JSScriptParser import JSScriptParser
from robocompscoutingapp.AppExceptions import JavaScriptParseError, JavaScriptParseWarning
from robocompscoutingapp.GlobalItems import getFullTemplateFile, rcsa_js_loader

def test_jSScriptPresent():
    parser = JSScriptParser(f"<script src='{rcsa_js_loader}'></script>")
    assert parser.jSScriptPresent() == True

    # Wrong script
    with pytest.raises(JavaScriptParseError):
        parser = JSScriptParser(f"<script src='wrong.js'></script>")
        parser.jSScriptPresent()

    # Too many
    with pytest.raises(JavaScriptParseError):
        parser = JSScriptParser(f"<script src='{rcsa_js_loader}'></script><script src='{rcsa_js_loader}'></script>")
        parser.jSScriptPresent()

def test_parse_element():
    #  Clean test
    parser = JSScriptParser(f"<script src='{rcsa_js_loader}'></script>")
    assert parser.parseElement().hasErrors() == False
    assert parser.parseElement().hasWarnings() == False

    # Wrong script
    parser = JSScriptParser(f"<script src='wrong.js'></script>")
    result = parser.parseElement()
    assert result.hasErrors() == True
    assert result.hasWarnings() == False

    # Too many
    parser = JSScriptParser(f"<script src='{rcsa_js_loader}'></script><script src='{rcsa_js_loader}'></script>")
    result = parser.parseElement()
    assert result.hasErrors() == True
    assert result.hasWarnings() == False
   
def test_validation_output(capfd):
    parser = JSScriptParser(f"<script src='{rcsa_js_loader}'></script>")
    result = parser.validate()
    assert result.hasErrors() == False
    assert result.hasWarnings() == False
    out, err = capfd.readouterr()
    assert out == "[+] Required Javascript tags are present!\n"

    