import React, { ReactFragment } from "react";

const DisclaimerAndExamples: React.FC = () => {
  return (
    <>
      <div className="mt-10 mx-7">
        <div className="font-bold text-emphasis mb-3 pb-1 text-lg">
          Example Queries:
        </div>
      </div>
      <div className="mx-4 sm:mx-0 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-2 mb-2">
        {[
          "Tell me a legal provision that can be invoked against a BLO not doing her duty.",
          "What is the role of sector magistrates and sector police officers during elections?",
          "What to do if an EVM stops working at a booth on election day?",
          "Top things that an Observer should check on the first day of their visit to a constituency.",
        ].map((query, index) => (
          <div
            key={index}
            className="p-2 mt-2 sm:mt-6 border border-gray-500 rounded text-gray-600 shadow text-center text-bold text-xs mx-2"
          >
            {query}
          </div>
        ))}
      </div>
      <div className="text-xs sm:text-sm text-center text-gray-600 bg-gray-200 p-2 sm:p-3 rounded-md mx-7 mt-10 sm:mt-20 m-2 sm:m-3">
        <p>
          <strong>Disclaimer</strong>: ElectionGPT is a prototype system.
          Answers may not always be reliable or correct. Consider checking
          source documents for important queries.
        </p>
      </div>
    </>
  );
};

export default DisclaimerAndExamples;
