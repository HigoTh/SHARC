clc
close all
clear all

file = 'system_dl_interf_power_per_mhz.csv';

mainFolderPath = './';
% Get information about all contents in the main folder
allContents = dir(mainFolderPath);


% Filter for directories and exclude '.' and '..'
subfolders = allContents([allContents.isdir]); % Get all directories
subfolderNames = {subfolders.name};
subfolderNames = subfolderNames(~ismember(subfolderNames, {'.', '..'}));

% Loop through each subfolder
for i = 1:numel(subfolderNames)
    currentSubfolderName = subfolderNames{i};
    fullSubfolderPath = fullfile(mainFolderPath, currentSubfolderName);
    % Perform operations within the current subfolder
    fprintf('Processing subfolder: %s\n', fullSubfolderPath);
    
    leg = split(fullSubfolderPath, '_');
    table = readtable( [ fullSubfolderPath '/' file ] );
    
    [ f_a, x_a ] = ecdf( table.samples + 20 - 5 );
    
    semilogy( x_a, 1 - f_a, 'Linewidth', 2, 'DisplayName', leg{4} );
    hold on    
    grid on
    ax = gca;
    ax.FontSize = 14;
    ax.TickLabelInterpreter = 'Latex';
    legend( 'Interpreter', 'Latex', 'Fontsize', 14, 'Location', 'Best' );
    
    ylim([7e-3,1]);
    ylabel('CCDF', 'Interpreter', 'Latex', 'Fontsize', 14 );
    xlabel('Interference (dBm/100 MHz)', 'Interpreter', 'Latex', 'Fontsize', 14 );
end
