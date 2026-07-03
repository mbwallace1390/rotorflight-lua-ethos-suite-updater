"""Safety hardening applied to the legacy updater implementation.

The updater began as a single-file GUI. Keeping these policies in a separate
module makes the target validation and file-sync behavior independently testable
without changing the existing UI and download code.
"""


def apply_hardening(core):
    """Install strict radio-target and fail-closed file-sync behavior."""
    os = core.os

    def has_ethos_cpuid_marker(self, root):
        return any(
            os.path.isfile(os.path.join(root, marker))
            for marker in ("flash.cpuid", "sdcard.cpuid", "radio.cpuid")
        )

    def has_ethos_marker_combo(self, root):
        radio_bin = os.path.isfile(os.path.join(root, "radio.bin"))
        models_dir = os.path.isdir(os.path.join(root, "models"))
        bitmaps_dir = os.path.isdir(os.path.join(root, "bitmaps"))
        return (
            (radio_bin and models_dir)
            or (radio_bin and bitmaps_dir)
            or (models_dir and bitmaps_dir)
        )

    def is_safe_radio_root(self, root, is_removable):
        """Require positive ETHOS identification before selecting a target.

        CPUID markers are authoritative on any volume. Legacy marker layouts
        are accepted only on removable media, preventing a generic fixed drive
        with a root-level scripts folder from being selected automatically.
        """
        if self._has_ethos_cpuid_marker(root):
            return True
        if not is_removable:
            return False
        if self._has_ethos_marker_combo(root):
            return True
        label = self._get_volume_label(root)
        return bool(
            label
            and label.strip().upper() == "RADIO"
            and os.path.isfile(os.path.join(root, "radio.bin"))
        )

    def iter_candidate_roots(self):
        seen = set()
        for root in list(self._iter_mount_roots()) + list(self._iter_lsblk_mounts()):
            root = os.path.normpath(root)
            if root in seen:
                continue
            seen.add(root)
            yield root

    def find_radio_volume_by_label(self, removable_only=True):
        target_label = "RADIO"
        if core.sys.platform == "win32":
            if core.win32api is None or core.win32file is None:
                return None
            drives = core.win32api.GetLogicalDriveStrings().split("\x00")[:-1]
            for drive in drives:
                try:
                    dtype = core.win32file.GetDriveType(drive)
                    is_removable = dtype == core.win32file.DRIVE_REMOVABLE
                    if removable_only and not is_removable:
                        continue
                    drive_root = drive if drive.endswith("\\") else drive + "\\"
                    label = self._get_volume_label(drive_root)
                    if not label or label.strip().upper() != target_label:
                        continue
                    if not os.path.isfile(os.path.join(drive_root, "radio.bin")):
                        continue
                    if self._is_safe_radio_root(drive_root, is_removable):
                        return drive_root
                except Exception:
                    continue
            return None

        for root in self._iter_safe_candidate_roots():
            is_removable = self._is_removable_mount(root)
            if removable_only and not is_removable:
                continue
            label = self._get_volume_label(root)
            if not label or label.strip().upper() != target_label:
                continue
            if not os.path.isfile(os.path.join(root, "radio.bin")):
                continue
            if self._is_safe_radio_root(root, is_removable):
                return root
        return None

    def find_radio_volume_by_markers(self, removable_only=True):
        if core.sys.platform == "win32":
            if core.win32api is None or core.win32file is None:
                return None
            drives = core.win32api.GetLogicalDriveStrings().split("\x00")[:-1]
            for drive in drives:
                try:
                    dtype = core.win32file.GetDriveType(drive)
                    is_removable = dtype == core.win32file.DRIVE_REMOVABLE
                    if removable_only and not is_removable:
                        continue
                    drive_root = drive if drive.endswith("\\") else drive + "\\"
                    if self._is_safe_radio_root(drive_root, is_removable):
                        return drive_root
                except Exception:
                    continue
            return None

        for root in self._iter_safe_candidate_roots():
            is_removable = self._is_removable_mount(root)
            if removable_only and not is_removable:
                continue
            if self._is_safe_radio_root(root, is_removable):
                return root
        return None

    def find_scripts_dir_on_drives(self, removable_only=True):
        """Find scripts only on a mount positively identified as ETHOS."""
        if core.sys.platform == "win32":
            if core.win32api is None or core.win32file is None:
                return None
            drives = core.win32api.GetLogicalDriveStrings().split("\x00")[:-1]
            for drive in drives:
                try:
                    dtype = core.win32file.GetDriveType(drive)
                    is_removable = dtype == core.win32file.DRIVE_REMOVABLE
                    if removable_only and not is_removable:
                        continue
                    drive_root = drive if drive.endswith("\\") else drive + "\\"
                    if not self._is_safe_radio_root(drive_root, is_removable):
                        continue
                    for folder in ("scripts", "script"):
                        scripts = os.path.join(drive_root, folder)
                        if os.path.isdir(scripts):
                            return os.path.normpath(scripts)
                except Exception:
                    continue
        else:
            for root in self._iter_safe_candidate_roots():
                is_removable = self._is_removable_mount(root)
                if removable_only and not is_removable:
                    continue
                if not self._is_safe_radio_root(root, is_removable):
                    continue
                for folder in ("scripts", "script"):
                    scripts = os.path.join(root, folder)
                    if os.path.isdir(scripts):
                        return os.path.normpath(scripts)

        scripts = self._find_scripts_dir_via_radio_label(
            removable_only=removable_only
        )
        if scripts:
            return scripts
        return self._find_scripts_dir_via_radio_markers(
            removable_only=removable_only
        )

    def file_sha256(self, path, chunk=1024 * 1024):
        digest = core.hashlib.sha256()
        with open(path, "rb", buffering=0) as source:
            while True:
                data = source.read(chunk)
                if not data:
                    break
                digest.update(data)
        return digest.hexdigest()

    def needs_copy_with_hash(self, src_file, dst_file, *_args, **_kwargs):
        """Compare content; FAT timestamp equality is not content equality."""
        try:
            src_stat = os.stat(src_file)
        except FileNotFoundError:
            return False
        try:
            dst_stat = os.stat(dst_file)
        except FileNotFoundError:
            return True
        if src_stat.st_size != dst_stat.st_size:
            return True
        try:
            return self._file_sha256(src_file) != self._file_sha256(dst_file)
        except Exception:
            return True

    def remove_stale_files_with_progress(self, src, dst, use_phase=False):
        """Delete stale files and abort the update on the first write failure."""
        if not os.path.isdir(dst):
            return True

        src_files = self._build_rel_file_map(src, ignore_package_manifest=True)
        dst_files = self._build_rel_file_map(dst)
        stale = [rel for rel in dst_files if rel not in src_files]
        total_stale = len(stale)
        self.log(f"  Total stale files to delete: {total_stale}")

        removed = 0
        for rel in stale:
            if not self.is_updating:
                return False
            file_path = dst_files.get(rel) or os.path.join(dst, rel)
            try:
                attempt = 0
                while True:
                    try:
                        os.remove(file_path)
                        break
                    except OSError as error:
                        attempt += 1
                        if getattr(error, "winerror", None) == 483 and attempt < 3:
                            core.time.sleep(0.5)
                            continue
                        raise
                removed += 1
                core.time.sleep(core.COPY_SETTLE_SECONDS)
                percent = (removed / total_stale) * 100 if total_stale else 100
                self.update_progress(
                    removed,
                    f"Removed stale {removed}/{total_stale} files ({percent:.1f}%)",
                )
                if removed % 10 == 0 or removed == total_stale:
                    self.log(f"  [DEL {removed}/{total_stale}] {rel}")
            except Exception as error:
                if getattr(error, "winerror", None) == 483:
                    self.log(
                        "  ⚠ Device error while deleting stale file "
                        f"{os.path.basename(file_path)}."
                    )
                    self.attempt_chkdsk(file_path)
                else:
                    self.log(f"  ✗ Failed to delete stale file {rel}: {error}")
                raise RuntimeError(
                    f"Could not delete stale radio file: {rel}"
                ) from error

        self._remove_empty_dirs(dst)
        return True

    def copy_tree_with_progress(self, src, dst, use_phase=False):
        """Copy changed files, verify them, and fail closed on write errors."""
        os.makedirs(dst, exist_ok=True)
        src_files = self._build_rel_file_map(src, ignore_package_manifest=True)
        total_files = len(src_files)
        self.log(f"  Total files to verify: {total_files}")

        to_copy = []
        checked = 0
        for rel, src_file in src_files.items():
            if not self.is_updating:
                return False
            dst_file = os.path.join(dst, rel)
            os.makedirs(os.path.dirname(dst_file), exist_ok=True)
            if self._needs_copy_with_hash(src_file, dst_file):
                to_copy.append((rel, src_file, dst_file))
            checked += 1
            if checked % 50 == 0 or checked == total_files:
                percent = (checked / total_files) * 100 if total_files else 100
                self.update_progress(
                    checked,
                    f"Verified {checked}/{total_files} files ({percent:.1f}%)",
                )

        self.log(f"  Changed/new files to copy: {len(to_copy)}")
        copied = 0
        for rel, src_file, dst_file in to_copy:
            if not self.is_updating:
                return False
            try:
                core.shutil.copy2(src_file, dst_file)
                if self._needs_copy_with_hash(src_file, dst_file):
                    raise OSError("destination verification failed after copy")
                copied += 1
                core.time.sleep(core.COPY_SETTLE_SECONDS)
                percent = (copied / len(to_copy)) * 100 if to_copy else 100
                self.update_progress(
                    copied,
                    f"Copied {copied}/{len(to_copy)} files ({percent:.1f}%)",
                )
                if copied % 10 == 0 or copied == len(to_copy):
                    self.log(f"  [COPY {copied}/{len(to_copy)}] {rel}")
            except Exception as error:
                if getattr(error, "winerror", None) == 483:
                    self.log(
                        "  ⚠ Device error while copying "
                        f"{os.path.basename(src_file)}."
                    )
                    self.attempt_chkdsk(dst_file)
                else:
                    self.log(
                        f"  ✗ Failed to copy {os.path.basename(src_file)}: {error}"
                    )
                raise RuntimeError(
                    f"Could not copy or verify radio file: {rel}"
                ) from error

        if not to_copy:
            self.log("  No changed files detected.")
        return True

    radio = core.RadioInterface
    radio._has_ethos_cpuid_marker = has_ethos_cpuid_marker
    radio._has_ethos_marker_combo = has_ethos_marker_combo
    radio._is_safe_radio_root = is_safe_radio_root
    radio._iter_safe_candidate_roots = iter_candidate_roots
    radio._find_radio_volume_by_label = find_radio_volume_by_label
    radio._find_radio_volume_by_markers = find_radio_volume_by_markers
    radio.find_scripts_dir_on_drives = find_scripts_dir_on_drives

    gui = core.UpdaterGUI
    gui._file_sha256 = file_sha256
    gui._needs_copy_with_hash = needs_copy_with_hash
    # Keep legacy private method names working for unchanged call sites.
    gui._file_md5 = file_sha256
    gui._needs_copy_with_md5 = needs_copy_with_hash
    gui.remove_stale_files_with_progress = remove_stale_files_with_progress
    gui.copy_tree_with_progress = copy_tree_with_progress
