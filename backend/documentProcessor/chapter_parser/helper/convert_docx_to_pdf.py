import subprocess
import os

def convert_docx_to_pdf(input_file_path, libreoffice_path, output_directory):
    """
    Convert DOCX file to PDF using LibreOffice Portable in headless mode.
    Returns a dictionary with status, message, and output file path.
    """
    try:
        output_file_path = os.path.join(output_directory, os.path.splitext(os.path.basename(input_file_path))[0] + ".pdf")

        command = [
            libreoffice_path,
            '--headless',
            '--convert-to', 'pdf',
            '--outdir', output_directory,
            input_file_path
        ]

        subprocess.run(command, check=True)

        return output_file_path
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"LibreOffice conversion failed: {str(e)}")