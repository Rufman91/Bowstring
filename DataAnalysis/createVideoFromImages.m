function createVideoFromImages()
    % Select multiple images using a GUI
    [filenames, pathname] = uigetfile({'*.jpg;*.png;*.bmp', 'Image Files (*.jpg, *.png, *.bmp)'}, ...
                                      'Select Images', 'MultiSelect', 'on');
    
    if isequal(filenames, 0)
        disp('No images selected. Exiting.');
        return;
    end
    
    % Ensure filenames is a cell array for consistency
    if ischar(filenames)
        filenames = {filenames};
    end
    
    % Sort filenames based on sequence numbers if present
    filenames = sort(filenames);
    numImages = length(filenames);
    
    % Set frame rate (adjust according to your needs)
    frameRate = 30; % frames per second
    timeStep = 1 / frameRate; % time step between frames in seconds
    
    % Create a VideoWriter object
    outputVideo = VideoWriter(fullfile(pathname, 'output_video.avi'));
    outputVideo.FrameRate = frameRate; 
    open(outputVideo);

    % Create a figure for displaying images
    hFig = figure('visible', 'off');
    
    % Initialize progress bar
    progressBar = waitbar(0, 'Processing images...');

    % Iterate through selected images and write them to the video
    for i = 1:numImages
        % Full path of the image
        imgPath = fullfile(pathname, filenames{i});
        
        % Read image
        img = imread(imgPath);
        
        % Calculate relative timestamp in seconds
        relativeTime = (i - 1) * timeStep;
        timestampStr = sprintf('%.2f seconds', relativeTime);
        
        % Display image with relative timestamp
        imshow(img, 'Parent', gca);
        hold on;
        text(10, 10, timestampStr, 'Color', 'white', 'FontSize', 12, 'FontWeight', 'bold');
        frame = getframe(gca);
        hold off;

        % Write the frame to the video
        writeVideo(outputVideo, frame);
        
        % Update progress bar
        waitbar(i / numImages, progressBar, sprintf('Processing image %d of %d...', i, numImages));
    end

    % Close the video file and progress bar
    close(outputVideo);
    close(progressBar);
    close(hFig);
    disp('Video created successfully!');
end
