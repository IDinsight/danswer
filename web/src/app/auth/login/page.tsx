import { HealthCheckBanner } from "@/components/health/healthcheck";
import { User } from "@/lib/types";
import {
  getCurrentUserSS,
  getAuthUrlSS,
  getAuthTypeMetadataSS,
  AuthTypeMetadata,
} from "@/lib/userSS";
import { redirect } from "next/navigation";
import { getWebVersion, getBackendVersion } from "@/lib/version";
import Image from "next/image";
import { SignInButton } from "./SignInButton";

const Page = async ({
  searchParams,
}: {
  searchParams?: { [key: string]: string | string[] | undefined };
}) => {
  const autoRedirectDisabled = searchParams?.disableAutoRedirect === "true";

  // catch cases where the backend is completely unreachable here
  // without try / catch, will just raise an exception and the page
  // will not render
  let authTypeMetadata: AuthTypeMetadata | null = null;
  let currentUser: User | null = null;
  try {
    [authTypeMetadata, currentUser] = await Promise.all([
      getAuthTypeMetadataSS(),
      getCurrentUserSS(),
    ]);
  } catch (e) {
    console.log(`Some fetch failed for the login page - ${e}`);
  }

  let web_version: string | null = null;
  let backend_version: string | null = null;
  try {
    [web_version, backend_version] = await Promise.all([
      getWebVersion(),
      getBackendVersion(),
    ]);
  } catch (e) {
    console.log(`Version info fetch failed for the login page - ${e}`);
  }

  // simply take the user to the home page if Auth is disabled
  if (authTypeMetadata?.authType === "disabled") {
    return redirect("/");
  }

  // if user is already logged in, take them to the main app page
  if (currentUser && currentUser.is_active && currentUser.is_verified) {
    return redirect("/");
  }

  // get where to send the user to authenticate
  let authUrl: string | null = null;
  if (authTypeMetadata) {
    try {
      authUrl = await getAuthUrlSS(authTypeMetadata.authType);
    } catch (e) {
      console.log(`Some fetch failed for the login page - ${e}`);
    }
  }

  if (authTypeMetadata?.autoRedirect && authUrl && !autoRedirectDisabled) {
    return redirect(authUrl);
  }

  return (
    <main>
      <div className="absolute top-10x w-full">
        <HealthCheckBanner />
      </div>
      <div className="min-h-screen flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-md w-full space-y-8">
          <div>
            <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-200">
              HubGPT 🤖
            </h2>
          </div>
          <div className="flex">
            {authUrl ? (
              <a
                href={authUrl || ""}
                className={
                  BUTTON_STYLE +
                  " focus:outline-none focus:ring-2 hover:bg-red-700 focus:ring-offset-2 focus:ring-red-500"
                }
              >
                Sign in with {OAUTH_NAME}
              </a>
            ) : (
              <button className={BUTTON_STYLE + " cursor-default"}>
                Sign in with {OAUTH_NAME}
              </button>
            )}
          </div>
          <h2 className="text-center text-xl font-bold mt-4">
            Log In to Danswer
          </h2>
          {authUrl && authTypeMetadata && (
            <SignInButton
              authorizeUrl={authUrl}
              authType={authTypeMetadata?.authType}
            />
          )}
        </div>
      </div>
      <div className="fixed bottom-4 right-4 z-50 text-slate-400 p-2">
        VERSION w{web_version} b{backend_version}
      </div>
    </main>
  );
};

export default Page;
