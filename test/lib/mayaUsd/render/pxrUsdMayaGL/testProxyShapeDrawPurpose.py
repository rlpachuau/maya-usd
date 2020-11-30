#!/pxrpythonsubst
#
# Copyright 2018 Pixar
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

from maya import cmds

import os
import sys
import unittest

import fixturesUtils


class testProxyShapeDrawPurpose(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # The test USD data is authored Z-up, so make sure Maya is configured
        # that way too.
        cmds.upAxis(axis='z')

        inputPath = fixturesUtils.setUpClass(__file__,
            initializeStandalone=False, loadPlugin=False)

        cls._testName = 'ProxyShapeDrawPurposeTest'
        cls._inputDir = os.path.join(inputPath, cls._testName)

        cls._testDir = os.path.abspath('.')

        cls._cameraName = 'MainCamera'

    def setUp(self):
        cmds.file(new=True, force=True)

        # To control where the rendered images are written, we force Maya to
        # use the test directory as the workspace.
        cmds.workspace(self._testDir, o=True)

    def _WriteViewportImage(self, outputImageName, suffix):
        # Make sure the hardware renderer is available
        MAYA_RENDERER_NAME = 'mayaHardware2'
        mayaRenderers = cmds.renderer(query=True, namesOfAvailableRenderers=True)
        self.assertIn(MAYA_RENDERER_NAME, mayaRenderers)

        # Make it the current renderer.
        cmds.setAttr('defaultRenderGlobals.currentRenderer', MAYA_RENDERER_NAME,
            type='string')
        # Set the image format to PNG.
        cmds.setAttr('defaultRenderGlobals.imageFormat', 32)
        # Set the render mode to shaded and textured.
        cmds.setAttr('hardwareRenderingGlobals.renderMode', 4)
        # Specify the output image prefix. The path to it is built from the
        # workspace directory.
        cmds.setAttr('defaultRenderGlobals.imageFilePrefix',
            '%s_%s' % (outputImageName, suffix),
            type='string')
        # Apply the viewer's color transform to the rendered image, otherwise
        # it comes out too dark.
        cmds.setAttr("defaultColorMgtGlobals.outputTransformEnabled", 1)

        # Do the render.
        cmds.ogsRender(camera=self._cameraName, currentFrame=True, width=960,
            height=540)

    def testDrawAndToggleDrawPurposeAttributes(self):
        """
        Tests drawing USD proxy shapes while changing their purpose-based draw
        attributes.
        """
        mayaSceneFile = '%s.ma' % self._testName
        mayaSceneFullPath = os.path.join(self._inputDir, mayaSceneFile)
        cmds.file(mayaSceneFullPath, open=True, force=True)

        # Force an initial draw to complete by switching frames.
        animStartTime = cmds.playbackOptions(query=True,
            animationStartTime=True)
        cmds.currentTime(animStartTime + 1.0, edit=True)

        proxyShapeNodeName = '|%s|PurposeCubesProxy|PurposeCubesProxyShape' % self._testName
        drawRenderPurposeAttrName = '%s.drawRenderPurpose' % proxyShapeNodeName
        drawProxyPurposeAttrName = '%s.drawProxyPurpose' % proxyShapeNodeName
        drawGuidePurposeAttrName = '%s.drawGuidePurpose' % proxyShapeNodeName

        # By default, only the "drawProxyPurpose" attribute should be enabled.
        self.assertFalse(cmds.getAttr(drawRenderPurposeAttrName))
        self.assertTrue(cmds.getAttr(drawProxyPurposeAttrName))
        self.assertFalse(cmds.getAttr(drawGuidePurposeAttrName))
        self._WriteViewportImage(self._testName, 'proxyToggleOn')

        cmds.setAttr(drawRenderPurposeAttrName, True)
        cmds.setAttr(drawGuidePurposeAttrName, True)
        self._WriteViewportImage(self._testName, 'allTogglesOn')

        cmds.setAttr(drawRenderPurposeAttrName, False)
        cmds.setAttr(drawProxyPurposeAttrName, False)
        cmds.setAttr(drawGuidePurposeAttrName, False)
        self._WriteViewportImage(self._testName, 'allTogglesOff')

        cmds.setAttr(drawRenderPurposeAttrName, True)
        self._WriteViewportImage(self._testName, 'renderToggleOn')

        cmds.setAttr(drawRenderPurposeAttrName, False)
        cmds.setAttr(drawGuidePurposeAttrName, True)
        self._WriteViewportImage(self._testName, 'guideToggleOn')


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(testProxyShapeDrawPurpose)

    results = unittest.TextTestRunner(stream=sys.__stderr__).run(suite)
    if results.wasSuccessful():
        exitCode = 0
    else:
        exitCode = 1
    # maya running interactively often absorbs all the output.  comment out the
    # following to prevent maya from exiting and open the script editor to look
    # at failures.
    cmds.quit(abort=True, exitCode=exitCode)
