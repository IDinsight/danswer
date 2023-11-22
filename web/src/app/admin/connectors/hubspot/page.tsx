"use client";

import * as Yup from "yup";
import { HubSpotIcon, TrashIcon } from "@/components/icons/icons";
import { TextFormField } from "@/components/admin/connectors/Field";
import { HealthCheckBanner } from "@/components/health/healthcheck";
import { CredentialForm } from "@/components/admin/connectors/CredentialForm";
import {
  Credential,
  ConnectorIndexingStatus,
  HubSpotConfig,
  HubSpotCredentialJson,
} from "@/lib/types";
import useSWR, { useSWRConfig } from "swr";
import { fetcher } from "@/lib/fetcher";
import { LoadingAnimation } from "@/components/Loading";
import { adminDeleteCredential, linkCredential } from "@/lib/credential";
import { ConnectorForm } from "@/components/admin/connectors/ConnectorForm";
import { ConnectorsTable } from "@/components/admin/connectors/table/ConnectorsTable";
import { usePopup } from "@/components/admin/connectors/Popup";
import { usePublicCredentials } from "@/lib/hooks";

const Main = () => {
  const { popup, setPopup } = usePopup();

  const { mutate } = useSWRConfig();
  const {
    data: connectorIndexingStatuses,
    isLoading: isConnectorIndexingStatusesLoading,
    error: isConnectorIndexingStatusesError,
  } = useSWR<ConnectorIndexingStatus<any, any>[]>(
    "/api/manage/admin/connector/indexing-status",
    fetcher
  );

  const {
    data: credentialsData,
    isLoading: isCredentialsLoading,
    isValidating: isCredentialsValidating,
    error: isCredentialsError,
    refreshCredentials,
  } = usePublicCredentials();

  if (
    isConnectorIndexingStatusesLoading ||
    isCredentialsLoading ||
    isCredentialsValidating
  ) {
    return <LoadingAnimation text="Loading" />;
  }

  if (isConnectorIndexingStatusesError || !connectorIndexingStatuses) {
    return <div>Failed to load connectors</div>;
  }

  if (isCredentialsError || !credentialsData) {
    return <div>Failed to load credentials</div>;
  }

  const hubSpotConnectorIndexingStatuses: ConnectorIndexingStatus<
    HubSpotConfig,
    HubSpotCredentialJson
  >[] = connectorIndexingStatuses.filter(
    (connectorIndexingStatus) =>
      connectorIndexingStatus.connector.source === "hubspot"
  );
  const hubSpotCredential: Credential<HubSpotCredentialJson> =
    credentialsData.filter(
      (credential) => credential.credential_json?.hubspot_access_token
    )[0];

  return (
    <>
      {popup}
      <p className="text-sm">
        This connector allows you to sync all your HubSpot Tickets into HubGPT.
      </p>

      <h2 className="font-bold mb-2 mt-6 ml-auto mr-auto">
        Step 1: Provide your Credentials
      </h2>

      {hubSpotCredential ? (
        <>
          <div className="flex mb-1 text-sm">
            <p className="my-auto">Existing Access Token: </p>
            <p className="ml-1 italic my-auto max-w-md truncate">
              {hubSpotCredential.credential_json?.hubspot_access_token}
            </p>
            <button
              className="ml-1 hover:bg-gray-700 rounded-full p-1"
              onClick={async () => {
                if (hubSpotConnectorIndexingStatuses.length > 0) {
                  setPopup({
                    type: "error",
                    message:
                      "Must delete all connectors before deleting credentials",
                  });
                  return;
                }
                await adminDeleteCredential(hubSpotCredential.id);
                refreshCredentials();
              }}
            >
              <TrashIcon />
            </button>
          </div>
        </>
      ) : (
        <>
          <p className="text-sm">
            To use the HubSpot connector, provide the HubSpot Access Token.
          </p>
          <div className="border-solid border-gray-600 border rounded-md p-6 mt-2">
            <CredentialForm<HubSpotCredentialJson>
              formBody={
                <>
                  <TextFormField
                    name="hubspot_access_token"
                    label="HubSpot Access Token:"
                    type="password"
                  />
                </>
              }
              validationSchema={Yup.object().shape({
                hubspot_access_token: Yup.string().required(
                  "Please enter your HubSpot Access Token"
                ),
              })}
              initialValues={{
                hubspot_access_token: "",
              }}
              onSubmit={(isSuccess) => {
                if (isSuccess) {
                  refreshCredentials();
                }
              }}
            />
          </div>
        </>
      )}

      <h2 className="font-bold mb-2 mt-6 ml-auto mr-auto">
        Step 2: Start indexing!
      </h2>
      {hubSpotCredential ? (
        !hubSpotConnectorIndexingStatuses.length ? (
          <>
            <p className="text-sm mb-2">
              Click the button below to start indexing! We will pull the latest
              tickets from HubSpot every <b>10</b> minutes.
            </p>
            <div className="flex">
              <ConnectorForm<HubSpotConfig>
                nameBuilder={() => "HubSpotConnector"}
                source="hubspot"
                inputType="poll"
                formBody={null}
                validationSchema={Yup.object().shape({})}
                initialValues={{}}
                refreshFreq={10 * 60} // 10 minutes
                onSubmit={async (isSuccess, responseJson) => {
                  if (isSuccess && responseJson) {
                    await linkCredential(responseJson.id, hubSpotCredential.id);
                    mutate("/api/manage/admin/connector/indexing-status");
                  }
                }}
              />
            </div>
          </>
        ) : (
          <>
            <p className="text-sm mb-2">
              HubSpot connector is setup! We are pulling the latest tickets from
              HubSpot every <b>10</b> minutes.
            </p>
            <ConnectorsTable<HubSpotConfig, HubSpotCredentialJson>
              connectorIndexingStatuses={hubSpotConnectorIndexingStatuses}
              liveCredential={hubSpotCredential}
              getCredential={(credential) => {
                return (
                  <div>
                    <p>{credential.credential_json.hubspot_access_token}</p>
                  </div>
                );
              }}
              onCredentialLink={async (connectorId) => {
                if (hubSpotCredential) {
                  await linkCredential(connectorId, hubSpotCredential.id);
                  mutate("/api/manage/admin/connector/indexing-status");
                }
              }}
              onUpdate={() =>
                mutate("/api/manage/admin/connector/indexing-status")
              }
            />
          </>
        )
      ) : (
        <>
          <p className="text-sm">
            Please provide your access token in Step 1 first! Once done with
            that, you can then start indexing all your HubSpot tickets.
          </p>
        </>
      )}
    </>
  );
};

export default function Page() {
  return (
    <div className="mx-auto container">
      <div className="mb-4">
        <HealthCheckBanner />
      </div>
      <div className="border-solid border-gray-600 border-b mb-4 pb-2 flex">
        <HubSpotIcon size={32} />
        <h1 className="text-3xl font-bold pl-2">HubSpot</h1>
      </div>
      <Main />
    </div>
  );
}
