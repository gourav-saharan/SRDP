import io
import os
import re
import tempfile
from collections import Counter
from datetime import datetime

import numpy as np
import pandas as pd


SUPPORTED_EXTENSIONS = (
    ".csv", ".txt", ".tsv", ".tab", ".dat", ".log", ".asc", ".prn", ".data",
    ".xlsx", ".xlsm", ".xltx", ".xltm", ".xls", ".xlsb", ".ods",
    ".json", ".jsonl", ".ndjson",
    ".html", ".htm",
    ".stmf",
    ".xtrp",
)

TEXT_ENCODINGS = ("utf-8-sig", "utf-8", "utf-16", "cp1252", "iso-8859-1")
CSV_SEPARATORS = (None, ",", ";", "\t", "|")
TEXT_SEPARATORS = (None, "\t", ",", ";", "|", r"\s+")
TEXT_TO_XLSX_EXTENSIONS = (".txt", ".tsv", ".tab", ".dat", ".log", ".asc", ".prn", ".data")


class FileLoadError(Exception):
    """Raised when a file exists but cannot be converted to tabular data."""


class DataManager:
    def __init__(self):
        # List of dicts: {"filepath": str, "tag": str, "df": DataFrame, "columns": list}
        self.files_data = []
        self.converted_dir = self._get_converted_dir()

    def load_file(self, filepath, tag):
        try:
            ext = os.path.splitext(filepath)[1].lower()
            warnings = []
            if ext not in SUPPORTED_EXTENSIONS:
                warnings.append(f"Extension '{ext or 'none'}' is not in the supported list. Automatic table detection was used.")

            original_filepath = filepath
            converted_filepath = None

            if ext == ".csv":
                df, import_details = self._read_csv(filepath)
            elif ext in TEXT_TO_XLSX_EXTENSIONS:
                df, import_details = self._convert_text_to_xlsx(filepath)
                converted_filepath = import_details.get("converted_filepath")
            else:
                df, import_details = self._read_file(filepath)

            df = self._clean_dataframe(df)
            if import_details.get("sheets_found", 0) > 1 and import_details.get("sheet"):
                warnings.append(
                    f"Workbook contains {import_details['sheets_found']} sheets. Loaded first usable sheet '{import_details['sheet']}'."
                )
            if converted_filepath:
                warnings.append("Text input was converted to XLSX internally before upload.")

            file_info = {
                "filepath": converted_filepath or filepath,
                "original_filepath": original_filepath,
                "converted_filepath": converted_filepath,
                "tag": tag,
                "df": df,
                "columns": list(df.columns),
                "rows": len(df),
                "format": ".xlsx" if converted_filepath else (ext or "unknown"),
                "source_format": ext or "unknown",
                "warnings": warnings,
                "import_details": import_details,
            }
            self.files_data.append(file_info)
            return True, f"Loaded {len(df):,} rows and {len(df.columns):,} columns."
        except FileLoadError as e:
            return False, f"{os.path.basename(filepath)}: {e}"
        except Exception as e:
            return False, f"{os.path.basename(filepath)}: Failed to load file: {e}"

    def _read_file(self, filepath):
        if not os.path.isfile(filepath):
            raise FileLoadError("File was not found.")

        if os.path.getsize(filepath) == 0:
            raise FileLoadError("File is empty.")

        ext = os.path.splitext(filepath)[1].lower()

        if ext == ".csv":
            return self._read_csv(filepath)

        if ext in (".xlsx", ".xlsm", ".xltx", ".xltm", ".xls", ".xlsb", ".ods"):
            return self._read_excel(filepath, ext)

        if ext in (".json", ".jsonl", ".ndjson"):
            return self._read_json(filepath, ext)

        if ext in (".html", ".htm"):
            return self._read_html(filepath)

        if ext == ".stmf":
            return self._read_stmf(filepath)

        if ext == ".xtrp":
            return self._read_xtrp(filepath)

        return self._read_text_table(filepath)

    def _get_converted_dir(self):
        candidates = []
        local_app_data = os.environ.get("LOCALAPPDATA")
        if local_app_data:
            candidates.append(os.path.join(local_app_data, "SRDP", "Converted_XLSX"))
        candidates.append(os.path.join(tempfile.gettempdir(), "SRDP", "Converted_XLSX"))

        for folder in candidates:
            try:
                os.makedirs(folder, exist_ok=True)
                return folder
            except OSError:
                continue

        return tempfile.gettempdir()

    def _convert_text_to_xlsx(self, filepath):
        raw_df, import_details = self._read_text_table(filepath)
        cleaned_df = self._clean_dataframe(raw_df)
        converted_path = self._write_converted_xlsx(filepath, cleaned_df, import_details)

        import_details = dict(import_details)
        import_details.update({
            "reader": "text converted to xlsx",
            "conversion": "txt_to_xlsx",
            "converted_filepath": converted_path,
            "original_filepath": filepath,
            "sheet": "Data",
            "engine": "openpyxl",
        })
        return cleaned_df, import_details

    def _write_converted_xlsx(self, filepath, df, import_details):
        base_name = os.path.splitext(os.path.basename(filepath))[0]
        safe_name = re.sub(r"[^A-Za-z0-9_.-]+", "_", base_name).strip("._") or "converted_data"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        converted_path = os.path.join(self.converted_dir, f"{safe_name}_{timestamp}.xlsx")

        try:
            with pd.ExcelWriter(converted_path, engine="openpyxl") as writer:
                df.to_excel(writer, sheet_name="Data", index=False)

                details_df = pd.DataFrame(
                    [
                        ("Original file", filepath),
                        ("Converted on", datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
                        ("Encoding", import_details.get("encoding", "")),
                        ("Separator", import_details.get("separator", "")),
                        ("Header", import_details.get("header", "")),
                        ("Rows", len(df)),
                        ("Columns", len(df.columns)),
                    ],
                    columns=["Property", "Value"],
                )
                details_df.to_excel(writer, sheet_name="Import Details", index=False)
        except Exception as e:
            raise FileLoadError(f"Text file was parsed, but XLSX conversion failed: {e}") from e

        return converted_path

    def _read_excel(self, filepath, ext):
        try:
            engine_by_ext = {
                ".xlsx": "openpyxl",
                ".xlsm": "openpyxl",
                ".xltx": "openpyxl",
                ".xltm": "openpyxl",
                ".xls": "xlrd",
                ".xlsb": "pyxlsb",
                ".ods": "odf",
            }
            engine = engine_by_ext.get(ext)
            sheets = pd.read_excel(filepath, sheet_name=None, header=None, engine=engine)
        except ImportError as e:
            package_by_ext = {
                ".xls": "xlrd",
                ".xlsb": "pyxlsb",
                ".ods": "odfpy",
            }
            package = package_by_ext.get(ext, "openpyxl")
            raise FileLoadError(f"{ext.upper().lstrip('.')} files require the optional '{package}' package.") from e
        except ValueError as e:
            package_by_ext = {
                ".xls": "xlrd",
                ".xlsb": "pyxlsb",
                ".ods": "odfpy",
            }
            if "Missing optional dependency" in str(e):
                package = package_by_ext.get(ext, "openpyxl")
                raise FileLoadError(f"{ext.upper().lstrip('.')} files require the optional '{package}' package.") from e
            raise FileLoadError(f"Excel support is missing: {e}") from e
        except Exception as e:
            raise FileLoadError(f"Excel file could not be read: {e}") from e

        for sheet_name, raw_df in sheets.items():
            table = self._extract_table(raw_df)
            cleaned = self._clean_dataframe(table, validate=False)
            if not cleaned.empty and len(cleaned.columns) >= 2:
                return cleaned, {
                    "reader": "spreadsheet",
                    "sheet": str(sheet_name),
                    "engine": engine or "auto",
                    "sheets_found": len(sheets),
                }

        raise FileLoadError("Workbook does not contain a readable table.")

    def _read_json(self, filepath, ext):
        attempts = []
        if ext in (".jsonl", ".ndjson"):
            attempts.append({"lines": True})
        attempts.extend(({}, {"lines": True}))

        for kwargs in attempts:
            try:
                df = pd.read_json(filepath, **kwargs)
                if isinstance(df, pd.Series):
                    df = df.to_frame()
                if not df.empty:
                    return df, {
                        "reader": "json lines" if kwargs.get("lines") else "json",
                        "mode": "records",
                    }
            except ValueError:
                continue

        raise FileLoadError("JSON file must contain records, an array of objects, or JSON Lines table data.")

    def _read_stmf(self, filepath):
        last_error = None
        for encoding in TEXT_ENCODINGS:
            try:
                df = pd.read_csv(
                    filepath,
                    sep="\t",
                    skiprows=50,
                    encoding=encoding,
                    engine="python",
                    on_bad_lines="skip"
                )
                return df, {
                    "reader": "stmf",
                    "encoding": encoding,
                    "separator": "tab",
                    "header": "row 51",
                }
            except UnicodeError:
                continue
            except Exception as e:
                last_error = e

        if last_error:
            raise FileLoadError(f"STMF data could not be parsed: {last_error}") from last_error
        raise FileLoadError("STMF data could not be parsed.")

    def _read_xtrp(self, filepath):
        try:
            with open(filepath, "rb") as f:
                data = f.read()
        except OSError as e:
            raise FileLoadError(f"XTRP file could not be opened: {e}") from e

        if len(data) < 8:
            raise FileLoadError("XTRP file is too small to contain measurement data.")

        channel_names = self._extract_xtrp_channel_names(data)
        if not channel_names:
            channel_names = ["XTRP Channel 1"]

        runs = self._extract_xtrp_float_runs(data)
        if not runs:
            raise FileLoadError("XTRP measurement blocks could not be detected.")

        channel_count = len(channel_names)
        channel_values = [[] for _ in range(channel_count)]
        for idx, values in enumerate(runs):
            channel_values[idx % channel_count].append(values)

        channel_series = []
        for idx, blocks in enumerate(channel_values):
            if blocks:
                series = pd.Series(pd.concat(blocks, ignore_index=True), dtype="float64")
            else:
                series = pd.Series(dtype="float64")
            channel_series.append(series)

        max_len = max((len(series) for series in channel_series), default=0)
        if max_len == 0:
            raise FileLoadError("XTRP measurement blocks did not contain usable samples.")

        sample_rate = self._extract_xtrp_sample_rate(data)
        df, metrics = self._build_xtrp_frequency_spectrum(channel_names, channel_series, sample_rate)

        return df, {
            "reader": "xtrp binary",
            "mode": "A-weighted frequency spectrum",
            "channels": channel_count,
            "sample_columns": ", ".join(channel_names),
            "samples": max_len,
            "sample_rate_hz": sample_rate,
            "xtrp_noise_metrics": metrics,
        }

    def _extract_xtrp_channel_names(self, data):
        unit_markers = [data.find(marker) for marker in (b'"Voltage"', b'"Pressure"', b'"Time"') if data.find(marker) != -1]
        search_end = min(unit_markers) if unit_markers else min(len(data), 65536)
        header = data[:search_end]

        matches = []
        for idx in range(0, max(0, len(header) - 3)):
            if header[idx:idx + 2] not in (b"\xba\x01", b"\xea\x01"):
                continue

            text_len = header[idx + 2]
            if text_len < 3 or text_len > 80 or idx + 3 + text_len > len(header):
                continue

            raw_text = header[idx + 3:idx + 3 + text_len]
            try:
                text = raw_text.decode("ascii").strip()
            except UnicodeDecodeError:
                continue

            if not text:
                continue
            if not any(ch.isalpha() for ch in text):
                continue
            if sum(ch.isalpha() for ch in text) < 3:
                continue
            if any(not (ch.isalnum() or ch in " _./()+-") for ch in text):
                continue

            matches.append((idx, text))

        counts = Counter(text for _, text in matches)
        names = []
        seen = set()
        ignored = {
            "SMD2",
            "Simcenter Testlab Scope",
            "CAN:XS",
        }
        for _, text in matches:
            if text in seen or text in ignored:
                continue
            if counts[text] < 2:
                continue
            names.append(text)
            seen.add(text)

        return names

    def _extract_xtrp_float_runs(self, data):
        usable_len = (len(data) // 4) * 4
        if usable_len == 0:
            return []

        try:
            float_values = np.frombuffer(data[:usable_len], dtype="<f4")
            plausible = (
                np.isfinite(float_values)
                & (np.abs(float_values) < 10000)
                & (np.abs(float_values) > 1e-12)
            )
            run_edges = np.diff(np.r_[0, plausible.astype("int8"), 0])
            starts = np.where(run_edges == 1)[0]
            ends = np.where(run_edges == -1)[0]
        except Exception as e:
            raise FileLoadError(f"XTRP numeric data could not be decoded: {e}") from e

        runs = []
        for start, end in zip(starts, ends):
            length = end - start
            if 512 <= length <= 65536:
                values = pd.Series(float_values[start:end].astype("float64"))
                if not values.empty and values.std(skipna=True) > 0:
                    runs.append(values)

        return runs

    def _extract_xtrp_sample_rate(self, data):
        sample_interval = b"\xbd\x1d\xe1\x36"
        count = data[:65536].count(sample_interval)
        if count >= 2:
            return 1.0 / np.frombuffer(sample_interval, dtype="<f4")[0].item()

        return 1.0

    def _build_xtrp_frequency_spectrum(self, channel_names, channel_series, sample_rate):
        spectra = {}
        metrics = {}
        frequency_axis = None

        for channel_name, series in zip(channel_names, channel_series):
            values = pd.to_numeric(series, errors="coerce").dropna().to_numpy(dtype=float)
            frequency, db_a, channel_metrics = self._xtrp_channel_spectrum(values, sample_rate)
            if frequency_axis is None:
                frequency_axis = frequency

            if frequency_axis is None or len(frequency_axis) == 0:
                continue

            if len(db_a) != len(frequency_axis):
                db_a = np.interp(frequency_axis, frequency, db_a, left=np.nan, right=np.nan)

            spectra[f"{channel_name} dB(A)"] = db_a
            metrics[channel_name] = channel_metrics

        if frequency_axis is None or not spectra:
            raise FileLoadError("XTRP frequency spectrum could not be calculated.")

        df = pd.DataFrame({"Frequency (Hz)": frequency_axis})
        for column, values in spectra.items():
            df[column] = values

        return df, metrics

    def _xtrp_channel_spectrum(self, values, sample_rate):
        if len(values) < 8:
            return np.array([]), np.array([]), {}

        values = values[np.isfinite(values)]
        values = values - np.mean(values)
        if len(values) < 8:
            return np.array([]), np.array([]), {}

        nperseg = min(32768, 2 ** int(np.floor(np.log2(len(values)))))
        nperseg = max(1024, nperseg)
        if len(values) < nperseg:
            nperseg = 2 ** int(np.floor(np.log2(len(values))))

        step = max(1, nperseg // 2)
        window = np.hanning(nperseg)
        scale = sample_rate * np.sum(window ** 2)
        psd_sum = None
        segment_count = 0

        for start in range(0, len(values) - nperseg + 1, step):
            segment = values[start:start + nperseg] * window
            spectrum = np.fft.rfft(segment)
            psd = (np.abs(spectrum) ** 2) / scale
            if nperseg > 1:
                psd[1:-1] *= 2
            psd_sum = psd if psd_sum is None else psd_sum + psd
            segment_count += 1

        if psd_sum is None or segment_count == 0:
            return np.array([]), np.array([]), {}

        psd = psd_sum / segment_count
        frequency = np.fft.rfftfreq(nperseg, d=1.0 / sample_rate)
        max_frequency = min(20000.0, sample_rate / 2)
        keep = (frequency > 0) & (frequency <= max_frequency)
        frequency = frequency[keep]
        psd = psd[keep]

        if len(frequency) == 0:
            return np.array([]), np.array([]), {}

        df = frequency[1] - frequency[0] if len(frequency) > 1 else max_frequency
        a_weighting_db = self._a_weighting_db(frequency)
        a_weighting_power = np.power(10.0, a_weighting_db / 10.0)
        bin_rms_a = np.sqrt(np.maximum(psd * df * a_weighting_power, 0))
        db_a = 20 * np.log10(np.maximum(bin_rms_a, 1e-20) / 0.00002)

        overall_rms_a = float(np.sqrt(np.sum(psd * df * a_weighting_power)))
        overall_db_a = self._to_db_spl(overall_rms_a)
        valid_db = db_a[np.isfinite(db_a)]
        p95_db_a = float(np.percentile(valid_db, 95)) if len(valid_db) else float("nan")
        peak_idx = int(np.nanargmax(db_a))
        peak_db_a = float(db_a[peak_idx])
        peak_frequency = float(frequency[peak_idx])
        sharp_peak_count = self._count_sharp_spectrum_peaks(db_a)

        return frequency, db_a, {
            "overall_db_a": overall_db_a,
            "p95_db_a": p95_db_a,
            "peak_db_a": peak_db_a,
            "peak_frequency_hz": peak_frequency,
            "sharp_peak_count": sharp_peak_count,
            "score": (0.55 * overall_db_a) + (0.25 * p95_db_a) + (0.15 * peak_db_a) + (0.10 * sharp_peak_count),
        }

    def _a_weighting_db(self, frequency):
        f2 = np.square(frequency)
        numerator = np.square(12200.0) * np.square(f2)
        denominator = (
            (f2 + np.square(20.6))
            * np.sqrt((f2 + np.square(107.7)) * (f2 + np.square(737.9)))
            * (f2 + np.square(12200.0))
        )
        return 20 * np.log10(np.maximum(numerator / denominator, 1e-20)) + 2.0

    def _to_db_spl(self, rms_value):
        if rms_value <= 0 or not np.isfinite(rms_value):
            return float("nan")
        return 20 * np.log10(rms_value / 0.00002)

    def _count_sharp_spectrum_peaks(self, db_values):
        if len(db_values) < 3:
            return 0

        values = pd.Series(db_values).replace([np.inf, -np.inf], np.nan).interpolate(limit_direction="both")
        baseline = values.rolling(window=31, center=True, min_periods=1).median().to_numpy(dtype=float)
        clean = values.to_numpy(dtype=float)
        high_level_floor = np.nanpercentile(clean, 95) + 3.0
        local_peak = (clean[1:-1] > clean[:-2]) & (clean[1:-1] >= clean[2:])
        prominent = (clean[1:-1] - baseline[1:-1]) >= 10.0
        high_enough = clean[1:-1] >= high_level_floor
        return int(np.sum(local_peak & prominent & high_enough))

    def _read_html(self, filepath):
        try:
            tables = pd.read_html(filepath)
        except ImportError as e:
            raise FileLoadError(f"HTML table support is missing: {e}") from e
        except Exception as e:
            raise FileLoadError(f"No readable HTML table was found: {e}") from e

        candidates = [self._clean_dataframe(table, validate=False) for table in tables]
        candidates = [table for table in candidates if not table.empty]
        if candidates:
            best = max(candidates, key=lambda table: table.shape[0] * max(1, table.shape[1]))
            return best, {
                "reader": "html table",
                "tables_found": len(tables),
            }

        raise FileLoadError("HTML file does not contain a readable table.")

    def _read_csv(self, filepath):
        last_error = None
        candidates = []

        for encoding in TEXT_ENCODINGS:
            for sep in CSV_SEPARATORS:
                for header in ("infer", None):
                    try:
                        df = pd.read_csv(
                            filepath,
                            sep=sep,
                            engine="python",
                            header=header,
                            on_bad_lines="skip",
                            encoding=encoding,
                        )
                        candidates.append((
                            self._score_table(df),
                            df,
                            {
                                "reader": "csv",
                                "encoding": encoding,
                                "separator": self._separator_label(sep),
                                "header": "detected" if header == "infer" else "generated",
                            },
                        ))
                    except UnicodeError as e:
                        last_error = e
                        break
                    except Exception as e:
                        last_error = e

        candidates = [(score, df, details) for score, df, details in candidates if score > 0]
        if candidates:
            candidates.sort(key=lambda item: item[0], reverse=True)
            return candidates[0][1], candidates[0][2]

        if last_error:
            raise FileLoadError(f"CSV data could not be parsed: {last_error}") from last_error
        raise FileLoadError("CSV data could not be parsed.")

    def _read_text_table(self, filepath):
        last_error = None

        for encoding in TEXT_ENCODINGS:
            try:
                with open(filepath, "r", encoding=encoding) as f:
                    text = f.read()
            except UnicodeError as e:
                last_error = e
                continue
            except OSError as e:
                raise FileLoadError(f"Text file could not be opened: {e}") from e

            text = self._normalise_text(text)
            candidates = []

            for candidate_text in self._text_variants(text):
                for sep in TEXT_SEPARATORS:
                    for header in ("infer", None):
                        try:
                            df = pd.read_csv(
                                io.StringIO(candidate_text),
                                sep=sep,
                                engine="python",
                                header=header,
                                on_bad_lines="skip",
                            )
                            candidates.append((
                                self._score_table(df),
                                df,
                                {
                                    "reader": "text table",
                                    "encoding": encoding,
                                    "separator": self._separator_label(sep),
                                    "header": "detected" if header == "infer" else "generated",
                                },
                            ))
                        except Exception as e:
                            last_error = e

                try:
                    df = pd.read_fwf(io.StringIO(candidate_text))
                    candidates.append((
                        self._score_table(df),
                        df,
                        {
                            "reader": "fixed width text",
                            "encoding": encoding,
                            "separator": "fixed width",
                            "header": "detected",
                        },
                    ))
                except Exception as e:
                    last_error = e

            candidates = [(score, df, details) for score, df, details in candidates if score > 0]
            if candidates:
                candidates.sort(key=lambda item: item[0], reverse=True)
                return candidates[0][1], candidates[0][2]

        if last_error:
            raise FileLoadError(f"Text data could not be parsed: {last_error}") from last_error
        raise FileLoadError("Text data could not be parsed.")

    def _separator_label(self, sep):
        labels = {
            None: "auto",
            "\t": "tab",
            ",": "comma",
            ";": "semicolon",
            "|": "pipe",
            r"\s+": "whitespace",
        }
        return labels.get(sep, str(sep))

    def _normalise_text(self, text):
        text = text.replace("\x00", "")
        lines = []
        for line in text.splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            if stripped.startswith("#") or stripped.startswith("//"):
                continue
            lines.append(line)
        return "\n".join(lines)

    def _text_variants(self, text):
        variants = [text]
        variants.extend(self._consistent_delimited_blocks(text, delimiter) for delimiter in ("\t", ",", ";", "|"))
        variants.append(self._consistent_whitespace_block(text))

        unique = []
        seen = set()
        for variant in variants:
            variant = variant.strip()
            if not variant or variant in seen:
                continue
            unique.append(variant)
            seen.add(variant)
        return unique

    def _consistent_delimited_blocks(self, text, delimiter):
        lines = [line for line in text.splitlines() if line.strip()]
        counts = [line.count(delimiter) for line in lines[:500] if line.count(delimiter) > 0]
        if not counts:
            return ""

        expected_delimiters = Counter(counts).most_common(1)[0][0]
        selected = [line for line in lines if line.count(delimiter) == expected_delimiters]
        return "\n".join(selected)

    def _consistent_whitespace_block(self, text):
        lines = [line for line in text.splitlines() if line.strip()]
        token_counts = [len(line.split()) for line in lines[:500] if len(line.split()) > 1]
        if not token_counts:
            return ""

        expected_tokens = Counter(token_counts).most_common(1)[0][0]
        selected = [line for line in lines if len(line.split()) == expected_tokens]
        return "\n".join(selected)

    def _score_table(self, df):
        try:
            df = self._clean_dataframe(df, validate=False)
        except Exception:
            return 0

        rows, cols = df.shape
        if rows == 0 or cols == 0:
            return 0

        numeric_ratio = self._numeric_ratio(df)
        score = rows * min(cols, 20)

        if cols == 1:
            score *= 0.15
        else:
            score *= 1.5

        score *= 1 + numeric_ratio

        if self._has_meaningful_headers(df):
            score *= 1.25

        return score

    def _numeric_ratio(self, df):
        sample = df.head(200)
        total = max(1, sample.size)
        numeric = 0
        for column in sample.columns:
            numeric += pd.to_numeric(sample[column], errors="coerce").notna().sum()
        return numeric / total

    def _has_meaningful_headers(self, df):
        meaningful = 0
        for column in df.columns:
            label = str(column).strip()
            if not label or label.lower().startswith("unnamed"):
                continue
            try:
                float(label)
                continue
            except ValueError:
                meaningful += 1
        return meaningful >= max(1, len(df.columns) // 2)

    def _extract_table(self, df):
        if df is None:
            return df

        df = df.copy()
        df.dropna(axis=0, how="all", inplace=True)
        df.dropna(axis=1, how="all", inplace=True)
        df.reset_index(drop=True, inplace=True)
        df.columns = range(len(df.columns))

        if df.empty:
            return df

        # Stop at a fully blank row after the table starts, which avoids pulling
        # unrelated notes or secondary blocks into the uploaded dataset.
        blank_rows = df.isna().all(axis=1)
        if blank_rows.any():
            first_blank_positions = [idx for idx, blank in enumerate(blank_rows.tolist()) if blank and idx > 0]
            if first_blank_positions:
                df = df.iloc[:first_blank_positions[0]].copy()

        return df

    def _clean_dataframe(self, df, validate=True):
        if df is None:
            raise FileLoadError("No table data was found.")

        if isinstance(df, pd.Series):
            df = df.to_frame()

        df = df.copy()
        df.dropna(axis=0, how="all", inplace=True)
        df.dropna(axis=1, how="all", inplace=True)
        df.reset_index(drop=True, inplace=True)

        if self._should_promote_first_row(df):
            header_row = df.iloc[0]
            df = df.iloc[1:].copy()
            df.columns = self._labels_from_row(header_row)
            df.dropna(axis=0, how="all", inplace=True)
            df.dropna(axis=1, how="all", inplace=True)
            df.reset_index(drop=True, inplace=True)

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = [
                " ".join(str(part).strip() for part in column if str(part).strip() and not str(part).startswith("Unnamed"))
                for column in df.columns
            ]

        df = self._drop_probable_units_row(df)

        cleaned_columns = []
        used = {}
        for idx, column in enumerate(df.columns, start=1):
            label = str(column).strip()
            if not label or label.lower() == "nan" or label.lower().startswith("unnamed"):
                label = f"Column {idx}"

            if label in used:
                used[label] += 1
                label = f"{label} ({used[label]})"
            else:
                used[label] = 1

            cleaned_columns.append(label)

        df.columns = cleaned_columns
        df.reset_index(drop=True, inplace=True)

        if validate:
            if df.empty:
                raise FileLoadError("No usable rows or columns were found.")
            if len(df.columns) < 2:
                raise FileLoadError("Only one column was detected. Please use a tabular file with at least X and Y columns.")

        return df

    def _drop_probable_units_row(self, df):
        if df is None or df.empty or len(df) < 3 or len(df.columns) < 5:
            return df

        if self._columns_are_generic(df.columns):
            return df

        first_row = df.iloc[0]
        first_non_empty = first_row.notna().sum()
        if first_non_empty < max(2, len(df.columns) * 0.1):
            return df

        first_text_ratio = self._text_ratio(first_row)
        remaining_numeric_ratio = self._numeric_ratio(df.iloc[1:].head(25))

        if first_text_ratio >= 0.6 and remaining_numeric_ratio >= 0.5:
            df = df.iloc[1:].copy()
            df.reset_index(drop=True, inplace=True)

        return df

    def _should_promote_first_row(self, df):
        if df is None or df.empty or len(df) < 2:
            return False

        columns_are_generic = self._columns_are_generic(df.columns)
        first_row = df.iloc[0]
        first_non_empty = first_row.notna().sum()

        if first_non_empty < 2:
            return False

        first_text_ratio = self._text_ratio(first_row)
        remaining = df.iloc[1:].head(25)
        remaining_numeric_ratio = self._numeric_ratio(remaining) if not remaining.empty else 0

        return columns_are_generic and first_text_ratio >= 0.5 and remaining_numeric_ratio >= 0.25

    def _columns_are_generic(self, columns):
        generic = 0
        total = len(columns)
        for idx, column in enumerate(columns, start=1):
            label = str(column).strip().lower()
            if label in ("", "nan"):
                generic += 1
            elif label.startswith("unnamed"):
                generic += 1
            elif label == f"column {idx}".lower():
                generic += 1
            else:
                try:
                    float(label)
                    generic += 1
                except ValueError:
                    pass
        return total > 0 and generic / total >= 0.6

    def _text_ratio(self, row):
        values = [value for value in row.tolist() if pd.notna(value)]
        if not values:
            return 0

        text_count = 0
        for value in values:
            try:
                float(str(value).strip())
            except ValueError:
                text_count += 1
        return text_count / len(values)

    def _labels_from_row(self, row):
        labels = []
        for idx, value in enumerate(row.tolist(), start=1):
            if pd.isna(value):
                labels.append(f"Column {idx}")
            else:
                label = str(value).strip()
                labels.append(label if label else f"Column {idx}")
        return labels

    def remove_file(self, idx):
        if 0 <= idx < len(self.files_data):
            self.files_data.pop(idx)

    def get_all_columns(self):
        all_cols = []
        for f in self.files_data:
            for c in f["columns"]:
                if c not in all_cols:
                    all_cols.append(c)
        return all_cols

    def combine_files(self):
        if not self.files_data:
            return False, "No data files loaded to combine."
        
        dfs = []
        combined_count = 0
        for f in self.files_data:
            if f.get("source_format") == "multiple":
                combined_count += 1
            else:
                dfs.append(f["df"])
                
        if not dfs:
            return False, "No valid raw data files found to combine (excluding already combined files)."
            
        if len(dfs) < 2:
            return False, "Please load at least 2 raw files to combine."
            
        try:
            combined_df = pd.concat(dfs, ignore_index=True)
            tag_name = f"Combined Data {combined_count + 1}"
            
            file_info = {
                "filepath": f"Combined_Data_{combined_count + 1}_Virtual_File",
                "original_filepath": f"Combined from {len(dfs)} files",
                "converted_filepath": None,
                "tag": tag_name,
                "df": combined_df,
                "columns": list(combined_df.columns),
                "rows": len(combined_df),
                "format": "virtual",
                "source_format": "multiple",
                "warnings": [],
                "import_details": {"reader": "pandas concat"},
            }
            self.files_data.append(file_info)
            return True, f"Combined {len(dfs)} raw files into {tag_name} with {len(combined_df)} rows and {len(combined_df.columns)} columns."
        except Exception as e:
            return False, f"Failed to combine files: {e}"
