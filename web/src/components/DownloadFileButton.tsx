import React, { useCallback } from "react";
import { FiDownload } from "react-icons/fi";

export function DownloadFile({ disabled }: { disabled?: boolean }) {
  const downloadFile = useCallback(async () => {
    if (disabled) return;

    // Replace with your actual API endpoint
    const apiEndpoint = "/api/manage/admin/connector/indexing-status";
    try {
      const response = await fetch(apiEndpoint);
      if (!response.ok) throw new Error("Network response was not ok.");
      const data = await response.json();

      const csvContent = data.reduce((csv: string, item: any) => {
        // Check if file_locations exist before calling map
        const fileLocations =
          item.connector?.connector_specific_config?.file_locations;
        if (!fileLocations) {
          return csv; // Skip this item or handle it as needed
        }

        // Map through file locations and extract filenames, each on a new line
        const fileNames = fileLocations
          .map((location: string) => `"${location.split("/").pop()}"`)
          .join("\n");
        return `${csv}${fileNames}\n`;
      }, "");

      // Add the header
      const header = "File Names\n";
      const finalCsvContent = header + csvContent.trim(); // Trim to remove the last newline character

      // Create a blob with CSV data
      const blob = new Blob([finalCsvContent], {
        type: "text/csv;charset=utf-8;",
      });
      const url = URL.createObjectURL(blob);

      // Create a temporary link to trigger the download
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", "fileNames.csv"); // Name the download file
      document.body.appendChild(link);
      link.click();
      if (link.parentNode) {
        link.parentNode.removeChild(link);
      }
    } catch (error) {
      console.error("Error downloading the file:", error);
    }
  }, [disabled]);

  return (
    <div
      className={`
        my-auto 
        flex 
        mb-1
        mt-5
        ${disabled ? "cursor-default" : "hover:bg-hover cursor-pointer"} 
        w-fit 
        p-2 
        rounded-lg
        border-border
        text-sm`}
      onClick={downloadFile}
    >
      <FiDownload className="mr-1 my-auto" />
      Download list of indexed filenames
    </div>
  );
}
