const { useState, useEffect } = React;

function Sidebar({ setActivePage }) {
  const pages = [
    "Dashboard",
    "Production Overview",
    "Equipment Performance",
    "Quality Control",
    "Customer Satisfaction",
  ];

  return (
    <div className="bg-gray-800 text-white w-64 space-y-6 py-7 px-2 absolute inset-y-0 left-0 transform -translate-x-full md:relative md:translate-x-0 transition duration-200 ease-in-out">
      <nav>
        {pages.map((page) => (
          <a
            key={page}
            href={
              page === "Dashboard"
                ? "#"
                : `/${page.toLowerCase().replace(" ", "_")}`
            }
            className="block py-2.5 px-4 rounded transition duration-200 hover:bg-gray-700 hover:text-white"
            onClick={(e) => {
              if (page === "Dashboard") {
                e.preventDefault();
                setActivePage(page);
              }
            }}
          >
            {page}
          </a>
        ))}
      </nav>
    </div>
  );
}

function Header({ user, onLogout }) {
  return (
    <header className="bg-white shadow">
      <div className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8 flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">
            {user.firstname} {user.lastname}
          </h1>
          <p className="text-sm text-gray-600">{user.role}</p>
        </div>
        <button
          onClick={onLogout}
          className="bg-red-500 hover:bg-red-700 text-white font-bold py-2 px-4 rounded"
        >
          Logout
        </button>
      </div>
    </header>
  );
}

function Dashboard() {
  const [user, setUser] = useState(null);
  const [activePage, setActivePage] = useState("Dashboard");

  useEffect(() => {
    fetch("/api/user")
      .then((response) => response.json())
      .then((data) => setUser(data))
      .catch((error) => console.error("Error fetching user data:", error));
  }, []);

  const handleLogout = () => {
    fetch("/logout")
      .then(() => (window.location.href = "/login"))
      .catch((error) => console.error("Error logging out:", error));
  };

  if (!user) {
    return <div>Loading...</div>;
  }

  return (
    <div className="flex h-screen bg-gray-100">
      <Sidebar setActivePage={setActivePage} />
      <div className="flex-1 flex flex-col overflow-hidden">
        <Header user={user} onLogout={handleLogout} />
        <main className="flex-1 overflow-x-hidden overflow-y-auto bg-gray-200">
          <div className="container mx-auto px-6 py-8">
            {activePage === "Dashboard" && (
              <div>
                <h2 className="text-2xl font-semibold mb-4">
                  Welcome to the Dashboard
                </h2>
                <p>
                  Select a category from the sidebar to view detailed
                  information.
                </p>
              </div>
            )}
            {/* Other page components will be added here */}
          </div>
        </main>
      </div>
    </div>
  );
}

ReactDOM.render(<Dashboard />, document.getElementById("root"));
