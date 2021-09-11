import os
import sys
import config
import subprocess

codeFolders = []
configPaths = []
def execute(command, wait_for_completion=True):
    child = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                             close_fds=True)
    if wait_for_completion:
        out, err = child.communicate()
        status = child.returncode
        return status, out, err
    else:
        return child


class ObfuscaterGenerator():
    def __init__(self, basePath, destPath):
        self.destPath = destPath
        self.basePath = basePath
        self.runTimePath = "/tmp/obfs_runtime"
        print(self.destPath)
        print(self.basePath)

    def generateRuntimeLibraries(self):
        if not os.path.exists(self.runTimePath):
            os.makedirs(self.runTimePath)
        status, out, err = execute(f"pyarmor runtime --enable-suffix --advanced 1 -O {self.runTimePath}")
        if status:
            print("Error in creating runtime obfuscation object Out: %s Err: %s" % (out, err))

    def generateObfuscCode(self):
        execute(f"rsync -azSP {self.basePath}/ {self.destPath}/ --exclude Code_Obfuscation --exclude .git --exclude .gitlab-ci.yml --delete")
        for codePath in config.CODE_PATH:
            path = os.path.join(self.basePath, codePath)
            if codePath == "framework":
                status, out, err = execute("cd %s;rm -rf dist;pyarmor obfuscate --runtime %s --recursive --output framework/dist/ framework/__init__.py;rm -rf dist/config.py" % (path, self.runTimePath))
                print(status, out, err)
            else:
                status, out, err = execute("cd %s;rm -rf dist;pyarmor obfuscate --runtime %s *.py;rm -rf dist/config.py" % (path, self.runTimePath))
            if status:
                print(status, err)
                sys.exit(-1)
            dstPath = os.path.join(self.destPath, codePath)
            if not os.path.exists(dstPath):
                os.makedirs(dstPath)
            distPath = "%s/dist" % path
            if codePath == "framework":
                s, o, e = execute("rsync -aSP %s/framework/dist/ %s/framework/" % (path, dstPath))
                execute("rsync -aSP %s/setup.py %s/" % (path, dstPath))
            else:
                execute("rm -rf %s/*" % dstPath)
                s, o, e = execute("rsync -aSP %s/* %s/" % (distPath, dstPath))
            if s:
                print(s, o, e)
            if codePath in config.CONFIG_PATH:
                execute("rsync -aSP %s/config.py %s/" % (path, dstPath))
            if codePath in config.EXCLUDE_FILES:
                for file in config.EXCLUDE_FILES[codePath]:
                    execute("rsync -aSP %s/%s %s/" % (path, file, dstPath))
            if codePath != "framework":
                srcFiles = os.listdir(path)
                for file in srcFiles:
                    dst_path = os.path.join(dstPath, file)
                    src_path = os.path.join(path, file)
                    if os.path.isdir(src_path) and os.path.basename(src_path) == "dist":
                        continue
                    if os.path.isdir(src_path):
                        if os.path.isdir(src_path):
                            if not os.path.exists(dst_path):
                                os.makedirs(dst_path)
                            execute("rsync -aSP %s/* %s/" % (src_path, dst_path))
                        else:
                            execute("rsync -aSP %s %s" % (src_path, dst_path))
                    else:
                        if not os.path.exists(dst_path):
                            execute("rsync -aSP %s %s" % (src_path, dst_path))
            #git diff --name-only 9f2e1f0fa9180ffbc494b1df67f6efe76bf3db18 3d9b2113164435bc19a33a7443c028ade44fcd98
            if os.path.exists(distPath):
                execute("rm -rf %s" % distPath)

        present_version = os.environ['CI_COMMIT_SHA']
        old_scanned_version = ''
        lastcommit_file = f"{self.destPath}/lastcommit"
        if os.path.exists(lastcommit_file):
            with open(lastcommit_file) as f:
                old_scanned_version = f.read().strip()
        # changed_files = []
        # removed_files = []
        # if old_scanned_version:
        #     status, out, err = execute(
        #         f"cd {self.basePath};git diff --diff-filter=MRCA --name-only {present_version} {old_scanned_version}")
        #     if not status and out:
        #         changed_files = [file.strip() for file in out.decode().strip().splitlines()]
        #     status, out, err = execute(
        #         f"cd {self.basePath};git diff --diff-filter=D --name-only {present_version} {old_scanned_version}")
        #     if not status and out:
        #         removed_files = [file.strip() for file in out.decode().strip().splitlines() if not os.path.exists(os.path.join(self.basePath, file))]
        # print("*" * 20 + " -- CHANGED FILES -- " + "*" * 20)
        # print(changed_files)
        # print("*" * 20 + " -- REMOVED FILES -- " + "*" * 20)
        # print(removed_files)
        # print("*" * 62)
        # if changed_files:
        #     for file in changed_files:
        #         if file.strip().endswith(".py") or file.strip() in removed_files:
        #             continue
        #         dst_path = os.path.join(self.destPath, file)
        #         src_path = os.path.join(self.basePath, file)
        #         execute("rsync -aSP %s %s" % (src_path, dst_path))
        # for file in removed_files:
        #     dst_path = os.path.join(self.destPath, file)
        #     src_path = os.path.join(self.basePath, file)
        #     # If file available in sorce skipping
        #     if os.path.exists(src_path):
        #         continue
        #     if os.path.exists(dst_path):
        #         execute(f"cd {self.destPath} git rm {file}")

        f = open(lastcommit_file, "w+")
        f.write(present_version)
        f.close()



if __name__ == "__main__":
    sourcePath = sys.argv[1]
    destPath = sys.argv[2]
    ins = ObfuscaterGenerator(sourcePath, destPath)
    ins.generateRuntimeLibraries()
    # ins = ObfuscaterGenerator("/root/cyberGit_Venu/cybercns_encrypt/codebase", "/root/cyberGit_Venu/smaster-srv")
    ins.generateObfuscCode()
