/** Read a selected PDF locally so page limits can be shown before upload. */
export const getPdfPageCount = async (file: File): Promise<number> => {
  const { getDocument, GlobalWorkerOptions } = await import("pdfjs-dist/legacy/build/pdf.mjs");
  GlobalWorkerOptions.workerSrc = new URL(
    "pdfjs-dist/legacy/build/pdf.worker.min.mjs",
    import.meta.url
  ).toString();
  const loadingTask = getDocument({ data: new Uint8Array(await file.arrayBuffer()) });

  try {
    return (await loadingTask.promise).numPages;
  } finally {
    await loadingTask.destroy();
  }
};
