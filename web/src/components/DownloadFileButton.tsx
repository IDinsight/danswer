import React, { useCallback } from "react";
import { FiDownload } from "react-icons/fi";
import { jsPDF } from "jspdf";
import "jspdf-autotable";

declare module "jspdf" {
  interface jsPDF {
    autoTable: (options: any) => jsPDF;
  }
}

export function DownloadFile({ disabled }: { disabled?: boolean }) {
  const downloadFile = useCallback(async () => {
    if (disabled) return;

    const apiEndpoint = "/api/manage/admin/connector/indexing-status";
    try {
      const response = await fetch(apiEndpoint);
      if (!response.ok) throw new Error("Network response was not ok.");
      const data = await response.json();

      const allFileNames = data.reduce((acc: string[], item: any) => {
        const fileLocations =
          item.connector?.connector_specific_config?.file_locations;
        if (!fileLocations) return acc;

        const fileNames = fileLocations.map((location: string) =>
          location.split("/").pop()
        );
        return [...acc, ...fileNames];
      }, []);

      // Make allFilenames lower case and then title case
      const titleFileNames = allFileNames.map((fileName: string) => {
        const lowerCaseFileName = fileName.toLowerCase();
        return lowerCaseFileName
          .split(" ")
          .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
          .join(" ");
      });

      // Sorting logic
      const keywords = [
        "Representation",
        "Rules",
        "Handbook",
        "Hand Book",
        "Manual",
        "Act",
      ];
      const sortedFileNames = titleFileNames.sort((a: string, b: string) => {
        const aIndex = keywords.findIndex((keyword) => a.includes(keyword));
        const bIndex = keywords.findIndex((keyword) => b.includes(keyword));
        if (aIndex !== -1 && bIndex !== -1) return aIndex - bIndex;
        if (aIndex !== -1) return -1;
        if (bIndex !== -1) return 1;
        return 0;
      });

      // Prepare data for the table
      const tableData: Array<Array<string>> = sortedFileNames.map(
        (fileName: string) => [fileName]
      );

      // Add serial numbers to the table
      tableData.forEach((item: Array<string>, index: number) => {
        item.unshift((index + 1).toString());
      });

      // Generate PDF with a table
      const doc = new jsPDF();

      // Adding a title for the table (optional)
      // doc.text("Mapped Files", 14, 15);

      doc.autoTable({
        startY: 20, // Adjust this value as needed for positioning after the title or other content
        head: [["Serial No.", "Mapped Filenames"]], // Column header
        body: tableData, // Data for the table
      });

      // Trigger the download
      doc.save("ElectionGPT Mapped Filenames.pdf");
    } catch (error) {
      console.error("Error downloading the file:", error);
    }
  }, [disabled]);

  return (
    <div
      onClick={downloadFile}
      className={`my-auto flex mb-1 mt-5 ${
        disabled ? "cursor-default" : "hover:bg-hover cursor-pointer"
      } w-fit p-2 rounded-lg border-border text-sm`}
    >
      <FiDownload className="mr-1 my-auto" />
      Download list of mapped documents
    </div>
  );
}
