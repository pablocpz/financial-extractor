import time
from pathlib import Path

from docling_core.types.doc import ImageRefMode, PictureItem

from docling.datamodel.base_models import InputFormat, ConversionStatus
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption
from openai import OpenAI
from dotenv import load_dotenv
import base64
import tempfile
import warnings
warnings.filterwarnings("ignore", message=".*pin_memory.*")

IMAGE_RESOLUTION_SCALE = 2.0

def _export_single_converted_document(conv_res, output_dir: Path) -> None:

    doc_filename = conv_res.input.file.stem

    # # Save page images
    # for _page_no, page in conv_res.document.pages.items():
    #     page_no = page.page_no
    #     page_image_filename = output_dir / f"{doc_filename}-{page_no}.png"
    #     with page_image_filename.open("wb") as fp:
    #         page.image.pil_image.save(fp, format="PNG")

    # Save images of figures and tables
    # picture_counter = 0
    # for element, _level in conv_res.document.iterate_items():
    #     if isinstance(element, PictureItem):
    #         picture_counter += 1
    #         element_image_filename = (
    #             output_dir / f"{doc_filename}-picture-{picture_counter}.png"
    #         )
    #         with element_image_filename.open("wb") as fp:
    #             element.get_image(conv_res.document).save(fp, "PNG")

    # Save markdown with externally referenced pictures
    md_filename = output_dir / f"{doc_filename}-with-no-image-refs.md"
    conv_res.document.save_as_markdown(md_filename) 
    # image_mode=ImageRefMode.REFERENCED
    try:
        num_pages = len(conv_res.document.pages)
    except Exception:
        num_pages = "unknown"
    print(
        f"[export] {doc_filename}: no saved images "
        # f"{picture_counter} picture(s). Markdown: {md_filename}"
    )


def file_data_extraction(reports_folder_name:str, output_folder_name:str):
    """
    Reads the reports temp folder and parses every document to markdown format with captioned images inside another new temp folder called /out
    
    """
    data_folder = Path(__file__).parent / reports_folder_name
    
    output_dir = output_folder_name
    # Ensure output directory exists
    

    # Collect all PDFs in the reports folder
    input_doc_paths = sorted(data_folder.glob("*.pdf"))
    if not input_doc_paths:
        print(f"No PDFs found in {data_folder}")
        return
    print(f"Found {len(input_doc_paths)} PDF(s) in {data_folder}:")
    for p in input_doc_paths:
        print(f"  - {p.name}")

    # Important: For operating with page images, we must keep them, otherwise the DocumentConverter
    # will destroy them for cleaning up memory.
    # This is done by setting PdfPipelineOptions.images_scale, which also defines the scale of images.
    # scale=1 correspond of a standard 72 DPI image
    # The PdfPipelineOptions.generate_* are the selectors for the document elements which will be enriched
    # with the image field
    pipeline_options = PdfPipelineOptions()
    # pipeline_options.images_scale = IMAGE_RESOLUTION_SCALE
    # pipeline_options.generate_page_images = True
    # pipeline_options.generate_picture_images = True
    pipeline_options.do_table_structure = True
    pipeline_options.do_formula_enrichment=True
    pipeline_options.table_structure_options.do_cell_matching=True
    
    print(
        "Pipeline options: "
        f"images_scale={pipeline_options.images_scale}, "
        f"page_images={pipeline_options.generate_page_images}, "
        f"picture_images={pipeline_options.generate_picture_images}, "
        f"table_structure={pipeline_options.do_table_structure}"
    )

    doc_converter = DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
        }
    )

    start_time = time.time()

    conv_results = doc_converter.convert_all(
        input_doc_paths,
        raises_on_error=False,
    )

    print(f"Starting conversion of {len(input_doc_paths)} document(s)...")

    # Export results per document, preserving original behavior for each file
    success_count = 0
    failure_count = 0
    total_count = 0
    for conv_res in conv_results:
        total_count += 1
        doc_name = getattr(getattr(conv_res, "input", None), "file", None)
        try:
            doc_display = doc_name.name if doc_name else str(doc_name)
        except Exception:
            doc_display = str(doc_name)
        print(f"[convert] Processing result {total_count}: {doc_display} -> {conv_res.status}")
        if conv_res.status == ConversionStatus.SUCCESS:
            success_count += 1
            _export_single_converted_document(conv_res, Path(output_dir))
        else:
            failure_count += 1
            # Still continue to process the rest
            print(f"[warning] Conversion did not fully succeed for: {doc_display}")

    
    
    # # Run describe_images_in_markdown for all markdown files in output_dir
    # output_dir_path = Path(output_dir)
    # print(f"Scanning for markdown files in {output_dir_path} to describe images...")
    # md_files = list(output_dir_path.glob("*.md"))
    # if not md_files:
    #     print(f"No markdown files found in {output_dir_path}.")

    # for md_file in md_files:
    #     print(f"Processing markdown file: {md_file}")
    #     describe_images_in_markdown(md_path=md_file)
    #     print(f"Finished describing images in: {md_file}")

    # # Verify no remaining local image references before deletion
    # remaining_refs = 0
    # image_pattern_verify = re.compile(r'!\[([^\]]*)\]\(((?:[^()]+|\([^()]*\))+?)\)')
    # for md_file in md_files:
    #     try:
    #         text = md_file.read_text(encoding="utf-8")
    #         for m in image_pattern_verify.finditer(text):
    #             _, path_val = m.groups()
    #             if not (path_val.startswith("http://") or path_val.startswith("https://")):
    #                 remaining_refs += 1
    #     except Exception as e:
    #         print(f"[verify] Failed to read {md_file}: {e}")

    # if remaining_refs > 0:
    #     print(f"[cleanup] Skipping deletion: {remaining_refs} local image reference(s) still present in markdown.")
    # else:
    #     # Delete all images (png/jpg/jpeg) in output_dir after processing is complete
    #     print(f"\n[cleanup] Deleting all images in {output_dir} (png/jpg/jpeg)...")
    #     deleted_count = 0
    #     for pattern in ("*.png", "*.jpg", "*.jpeg"):
    #         for img_path in output_dir_path.rglob(pattern):
    #             try:
    #                 os.remove(img_path)
    #                 deleted_count += 1
    #                 print(f"[cleanup] Deleted: {img_path}")
    #             except Exception as e:
    #                 print(f"[cleanup] Failed to delete {img_path}: {e}")
    #     print(f"[cleanup] Image cleanup completed. Deleted {deleted_count} file(s).")
    
    end_time = time.time() - start_time

    print(
        f"\nProcessed {total_count} document(s). Successful: {success_count}, "
        f"Failed/partial: {failure_count}. "
        f"Elapsed: {end_time:.2f} seconds."
    )
    
    

import re
import os

# def describe_images_in_markdown(md_path):
#     """
#     For a markdown file, replaces each image link with a description generated by the OpenAI vision model.
#     The image links must be local paths.
#     The markdown is updated in-place. Each image reference is replaced in-place by its caption.

#     Args:
#         md_path (str or Path): Path to the markdown file.
#     """
#     from pathlib import Path

#     md_path = Path(md_path)
#     with md_path.open("r", encoding="utf-8") as f:
#         md_text = f.read()

#     # Regex to find markdown image links: ![alt](path)
#     # Supports parentheses inside the path (e.g., filename like "..._v3_(1)...")
#     image_pattern = re.compile(r'!\[([^\]]*)\]\(((?:[^()]+|\([^()]*\))+?)\)')

#     matches = list(image_pattern.finditer(md_text))
#     print(f"[images] {md_path.name}: found {len(matches)} image reference(s)")

#     def replace_image(match):
#         alt_text, img_path = match.groups()
#         # Only process local images (not http/https)
#         if img_path.startswith("http://") or img_path.startswith("https://"):
#             print(f"[images] Skipping remote image: {img_path}")
#             return match.group(0)
#         # Resolve image path; try multiple candidates to handle nested 'out/'
#         path_obj = Path(img_path)
#         candidate_paths = []
#         if path_obj.is_absolute():
#             candidate_paths.append(path_obj)
#         else:
#             # Project-root relative using current working directory
#             if img_path.startswith("out/"):
#                 candidate_paths.append((Path.cwd() / img_path).resolve())
#                 # If markdown sits in 'out/', also try stripping the leading 'out/'
#                 candidate_paths.append((md_path.parent / img_path[len("out/"):]).resolve())
#             # Relative to the markdown file location
#             candidate_paths.append((md_path.parent / img_path).resolve())

#         img_full_path = next((p for p in candidate_paths if p.exists()), None)
#         if img_full_path is None:
#             print(f"[images] Not found on disk, leaving unchanged: {img_path}")
#             return match.group(0)  # leave unchanged if not found
#         try:
#             print(f"[images] Describing: {img_full_path}")
#             description = openai_vision_model(str(img_full_path))
#         except Exception as e:
#             print(f"[images] Description failed for {img_full_path}: {e}")
#             description = f"[Image description failed: {e}]"
#         # Replace the entire image markdown with just the description (no image ref remains)
#         return f"\n{description}\n"

#     # Replace all image links with their descriptions (removing the image markdown entirely)
#     new_md_text = image_pattern.sub(replace_image, md_text)

#     # Write back to the same file (overwrite)
#     with md_path.open("w", encoding="utf-8") as f:
#         f.write(new_md_text)

#     # No deletion here; cleanup is handled after processing all markdown files



# def openai_vision_model(image_path):
#     """
#     Given a local image path, returns a description using OpenAI's vision model.
#     This is a placeholder; you must implement the actual OpenAI API call.
#     """
#     load_dotenv()


#     with open(image_path, "rb") as img_file:
#         img_bytes = img_file.read()
#         img_b64 = base64.b64encode(img_bytes).decode("utf-8")

    
#     client = OpenAI()

#     prompt = """
#     Prompt:
#     You are a financial-report captioner. Given a chart/graphic, output one concise, factual caption (≤25 words) describing chart type, key metric, time span, and main trend. No speculation or recommendations.

#     Format:
    
#     [Image Caption:]
#     ⸻
#     """
#     print(f"[openai] Requesting vision description for: {image_path}")
#     response = client.responses.create(
#     model="gpt-4.1",
#     input=[
#         {
#             "role": "user",
#             "content": [
#                 { "type": "input_text", "text": prompt},
#                 {
#                     "type": "input_image",
#                     "image_url": f"data:image/jpeg;base64,{img_b64}",
#                     },
#                 ],
#             }
#         ],
#     )


#     # print(response.output_text)
    
#     return response.output_text



if __name__ == "__main__":
    import time
    start_time = time.time()
    file_data_extraction(reports_folder_name="aaajajaja", output_folder_name="aaajajaja")
    elapsed = time.time() - start_time
    print(f"file_data_extraction completed in {elapsed:.2f} seconds")