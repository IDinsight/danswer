import { DownloadFile } from "../DownloadFileButton";

const DisclaimerAndExamples: React.FC<{
  onExampleClick: (query: string) => void;
}> = ({ onExampleClick }) => {
  return (
    <>
      <div className="mt-10 mx-7">
        <div className="font-bold text-emphasis mb-3 pb-1 text-lg">
          Example Queries:
        </div>
        <div className="mx-4 sm:mx-0 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2 mb-2">
          {[
            "How many flags are allowed per vehicle while MCC is in force?",
            "Which legal provisions empower the DEO to requisition private vehicles during elections?",
            "When do SSTs and FSTs start functioning and what are their key responsibilities?",
          ].map((query, index) => (
            <div
              key={index}
              className="p-2 mt-2 sm:mt-6 border border-gray-500 rounded text-gray-600 shadow text-center text-bold text-xs mx-2 cursor-pointer hover:bg-gray-200"
              onClick={() => onExampleClick(query)}
            >
              {query}
            </div>
          ))}
        </div>
      </div>
      <div className="text-xs sm:text-sm text-center text-gray-600 bg-gray-200 p-2 sm:p-3 rounded-md mx-7 mt-10 sm:mt-20 m-2 sm:m-3">
        <p>
          <strong>Disclaimer</strong>: ElectionGPT is a prototype system.
          Answers may not always be reliable or correct. Consider checking
          source documents for important queries.
        </p>
        <br />
        <p>
          Please use this{" "}
          <a
            href="https://forms.gle/qe9di633K3P7yijo7"
            style={{ textDecoration: "underline", fontWeight: "bold" }}
          >
            form
          </a>{" "}
          to give us detailed feedback.
        </p>
      </div>
      <div className="flex justify-center items-center">
        <DownloadFile />
      </div>
    </>
  );
};

export default DisclaimerAndExamples;
