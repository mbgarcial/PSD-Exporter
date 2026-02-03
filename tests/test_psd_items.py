import pytest
import sys
sys.path.append("..")
from psd_funcs import *
from psd_reader1 import *

# TESTS for psd_funcs



# ExportInfo
def test_ExportInfo_basic():
    export = ExportInfo("holi")
    assert export.name == "holi"
    export.path = "lala/lala/"
    assert export.path == "lala/lala/"

def test_resize():
    export = ExportInfo("holi", (200,300))
    export.resize(width=100)
    assert export.size == (100,150)
    export.resize(height = 300)
    assert export.size == (200,300)

    assert export.height == 300
    assert export.width == 200

    export.height = 150
    assert export.width == 100
    export.keepratio = False
    export.height = 300
    assert export.width == 100
    assert export.size == (100,300)


# PSDItem -----------

def test_PSDItem():
    item = PSDItem("root","layer1")
    assert item.parent == "root"
    assert item.name == "layer1"
    assert item.export == True

def test_PSDItem_toggle_export():
    item = PSDItem("root","layer1")
    assert item.export == True
    item.toggle_export()
    assert item.export == False
    item.toggle_export()
    assert item.export == True
    item.toggle_export(True)
    assert item.export == True

def test_PSDItem_skip():
    item = PSDItem("root","layer1")
    assert item.export == True
    assert item.ignore == False

    item.skip()
    assert item.export == False
    assert item.ignore == True

    item.not_skip()
    assert item.export == True
    assert item.ignore == False

def test_PSDItem_export_check():
    item = PSDItem("root","layer1")
    item2 = PSDItem("root","layer2", visible = False)
    item3 = PSDItem("root","layer3", ignore = True)
    item4 = PSDItem("root","layer4", export = False)
    item5 = PSDItem("root","layer5", ignore = False, export = False)
    assert item.export_check() == "export"
    assert item2.export_check(True) == "skip"
    assert item3.export_check() == "skip"
    assert item4.export_check() == "skip"
    assert item5.export_check() == "skip"

def test_PSDFolder_export_check():
    folder1 = PSDFolder("root","folder1")
    folder2 = PSDFolder("root","folder2", ignore = False, export = False)
    folder3 = PSDFolder("root","folder3", ignore = True, export = True)
    assert folder1.export_check() == "export"
    assert folder2.export_check() == "pass"
    assert folder3.export_check() == "skip"

def test_PSDFolder_add_item():
    folder1 = PSDFolder("root","folder1")
    layer1 = PSDLayer("poto","layer1")
    folder2 = PSDLayer("lala","folder2")
    assert layer1.parent == "poto"
    folder1.add_item(layer1)
    assert layer1 in folder1.contents
    assert folder1.contents[-1].parent == "folder1"
    assert folder2.parent == "lala"
    folder1.add_item(folder2)
    assert folder1.contents[-1].parent == "folder1"


# Basic PSD reading -------------

def test_read_psd():
    a = read_psd("psd_test.psd")
    assert a != {}
    assert read_psd("poto.psd") == {}

def test_read_psd_keys():
    d = read_psd("psd_test.psd")

    assert d != {}
    assert d["psd"]
    assert d["psd_name"] != ""
    assert d["psd_name"] == "psd_test.psd"

def test_folderlist():
    a = read_psd("psd_test.psd")
    folders = folderlist(a["psd"])
    assert folders
    assert folders != []
    assert "group1" in folders
    assert "group2" in folders
    assert "attr3" in folders
    assert "attr2" not in folders

def test_layerlist():
    a = read_psd("psd_test.psd")
    layers = layerlist(a["psd"])
    assert layers
    assert layers != []
    assert "group1" not in layers
    assert "group2" not in layers
    assert "attr3" not in layers
    assert "attr2" in layers

def test_foldercount():
    psd = read_psd("psd_test.psd")["psd"]
    count = foldercount(psd)
    assert count == 3
    

